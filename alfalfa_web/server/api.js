import AWS from "aws-sdk";
import { v1 as uuidv1 } from "uuid";
import { Advancer } from "./advancer";
import { del, mapHaystack, reduceById, scan } from "./utils";

class AlfalfaAPI {
  constructor(db, redis) {
    this.models = db.collection("model");
    this.points = db.collection("point");
    this.recs = db.collection("recs");
    this.runs = db.collection("run");
    this.simulations = db.collection("simulation");
    this.sites = db.collection("site");

    this.redis = redis;
    this.pub = redis.duplicate();
    this.sub = redis.duplicate();
    this.advancer = new Advancer(this.redis, this.pub, this.sub);

    AWS.config.update({ region: process.env.REGION || "us-east-1" });
    this.sqs = new AWS.SQS();
  }

  listSites = async () => {
    try {
      const runs = [];

      const models = (await this.models.find().toArray()).reduce(reduceById, {});
      const sites = (await this.sites.find().toArray()).map(mapHaystack).reduce(reduceById, {});

      for await (const run of this.runs.find()) {
        runs.push({
          id: run.ref_id,
          name: sites[run.site]?.dis,
          status: run.status.toLowerCase(),
          uploadTimestamp: run.created,
          uploadPath: models[run.model].path
        });
      }
      return runs;
    } catch (e) {
      console.error(e);
      return Promise.reject();
    }
  };

  findSite = async (siteRef) => {
    try {
      const run = await this.runs.findOne({ ref_id: siteRef });
      if (run) {
        const model = await this.models.findOne({ _id: run.model });
        const site = mapHaystack(await this.sites.findOne({ _id: run.site }));

        return {
          id: run.ref_id,
          name: site?.dis,
          status: run.status.toLowerCase(),
          uploadTimestamp: run.created,
          uploadPath: model.path
        };
      }
    } catch (e) {
      console.error(e);
      return Promise.reject();
    }
  };

  removeSite = async (siteRef) => {
    try {
      // Delete site
      const { value: site } = await this.sites.findOneAndDelete({ ref_id: siteRef });

      // Delete points
      for await (const run of this.runs.find({ site: site._id })) {
        await this.points.deleteMany({ run: run._id });
      }

      // Delete runs
      await this.runs.deleteMany({ site: site._id });

      // Delete recs
      await this.recs.deleteMany({ site: site._id });

      // Delete simulations
      await this.simulations.deleteMany({ site: site._id });

      // Delete redis keys
      const keys = await scan(this.redis, `site:${siteRef}*`);
      if (keys.length) await del(this.redis, keys);
    } catch (e) {
      console.error(e);
      return Promise.reject();
    }
  };

  startRun = async (siteRef, data) => {
    try {
      const { sim_type, status } = await this.runs.findOne({ ref_id: siteRef });

      if (status !== "READY") {
        return {
          error: "Run is not in 'READY' state"
        };
      }

      const { startDatetime, endDatetime, timescale, realtime, externalClock } = data;

      const messageBody = {
        job: `alfalfa_worker.jobs.${sim_type === "MODELICA" ? "modelica" : "openstudio"}.StepRun`,
        params: {
          run_id: siteRef,
          start_datetime: startDatetime,
          end_datetime: endDatetime,
          timescale: String(timescale || 5),
          realtime: String(!!realtime),
          external_clock: String(!!externalClock)
        }
      };
      const params = {
        MessageBody: JSON.stringify(messageBody),
        QueueUrl: process.env.JOB_QUEUE_URL,
        MessageGroupId: "Alfalfa"
      };
      await this.sqs.sendMessage(params).promise();
    } catch (e) {
      console.error(e);
      return Promise.reject();
    }
  };

  advanceRun = async (siteRef) => {
    try {
      await this.advancer.advance([siteRef]);
    } catch (e) {
      console.error(e);
      return Promise.reject();
    }
  };

  stopRun = async (siteRef) => {
    try {
      await this.recs.updateOne({ ref_id: siteRef }, { $set: { "rec.simStatus": "s:Stopping" } });
      this.pub.publish(siteRef, JSON.stringify({ message_id: uuidv1(), method: "stop" }));
    } catch (e) {
      console.error(e);
      return Promise.reject();
    }
  };
}

module.exports = AlfalfaAPI;
