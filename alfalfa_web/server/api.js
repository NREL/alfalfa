import AWS from "aws-sdk";
import { v1 as uuidv1 } from "uuid";
import { writePoint } from "./dbops";
import { del, getHashValue, getPointKey, mapHaystack, reduceById, scan, setHashValue, getHash } from "./utils";

class AlfalfaAPI {
  constructor(db, redis) {
    this.db = db;
    this.models = db.collection("model");
    this.points = db.collection("point");
    this.recs = db.collection("recs");
    this.runs = db.collection("run");
    this.simulations = db.collection("simulation");
    this.sites = db.collection("site");
    this.aliases = db.collection("alias");

    this.redis = redis;
    this.pub = redis.duplicate();
    this.sub = redis.duplicate();

    AWS.config.update({ region: process.env.REGION || "us-east-1" });
    this.sqs = new AWS.SQS();
    this.s3 = new AWS.S3({ endpoint: process.env.S3_URL });
  }

  listSites = async () => {
    try {
      const runs = [];

      const models = (await this.models.find().toArray()).reduce(reduceById, {});
      const sites = (await this.sites.find().toArray()).map(mapHaystack).reduce(reduceById, {});

      for await (const run of this.runs.find()) {
        const model = models[run.model];
        runs.push({
          id: run.ref_id,
          name: sites[run.site]?.dis,
          status: run.status.toLowerCase(),
          uploadTimestamp: run.created,
          uploadPath: `uploads/${model.ref_id}/${model.model_name}`,
          errorLog: run.error_log
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
          uploadPath: `uploads/${model.ref_id}/${model.model_name}`,
          errorLog: run.error_log
        };
      }
    } catch (e) {
      console.error(e);
      return Promise.reject();
    }
  };

  getSiteTime = async (siteRef) => {
    try {
      return await getHashValue(this.redis, siteRef, "sim_time");
    } catch (e) {
      return Promise.reject();
    }
  };

  listPoints = async (siteRef, pointType, getValue = false) => {
    try {
      const points = [];
      const run = await this.runs.findOne({ ref_id: siteRef });
      if (run) {
        const query = { run: run._id };
        if (pointType) {
          query.point_type = pointType;
        }
        for await (const point of this.points.find(query)) {
          const pointDict = {
            id: point.ref_id,
            name: point.name,
            type: point.point_type
          };
          if (getValue && point.point_type !== "INPUT") {
            pointDict.value = await this.readOutputPoint(siteRef, point.ref_id);
          }
          points.push(pointDict);
        }
        return points;
      }
    } catch (e) {
      console.error(e);
      return Promise.reject();
    }
  };

  readOutputPoint = async (siteRef, pointId) => {
    const key = getPointKey(siteRef, pointId) + ":out";
    const value = await getHashValue(this.redis, key, "curVal");
    if (value) {
      return parseFloat(value.replace(/^[a-z]:/, ""));
    }
    return null;
  };

  writeInputPoint = async (siteRef, pointId, value) => {
    const run = this.runs.findOne({ ref_id: siteRef });
    const point = this.points.findOne({ run: run._id, ref_id: pointId });

    if (point.point_type === "OUTPUT") {
      return Promise.reject("Cannot write to an Output point");
    }
    return writePoint(pointId, siteRef, 1, value, this.db, this.redis);
  };

  pointIdFromName = async (siteRef, pointName) => {
    const run = await this.runs.findOne({ ref_id: siteRef });
    return (await this.points.findOne({ run: run._id, name: pointName })).ref_id;
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
    return await this.sendRunMessage(siteRef, "advance");
  };

  stopRun = async (siteRef) => {
    try {
      return await this.sendRunMessage(siteRef, "stop");
    } catch (e) {
      console.error(e);
      return Promise.reject();
    }
  };

  sendRunMessage = (siteRef, method, data = null, timeout = 6000, pollingInterval = 100) => {
    return new Promise((resolve) => {
      const message_id = uuidv1();
      this.pub.publish(siteRef, JSON.stringify({ message_id: message_id, method: method, data: data }));
      const send_time = Date.now();

      let interval;

      const finalize = (success, message = "") => {
        clearInterval(interval);
        resolve({ status: success, message: message });
      };

      interval = setInterval(async () => {
        if (Date.now() - timeout > send_time) {
          finalize(false, "no simulation reply");
        }
        const response = await getHashValue(this.redis, siteRef, message_id);
        if (!response) return;
        finalize(JSON.parse(response).status === "ok", response);
      }, pollingInterval);
    });
  };

  listModels = async () => {
    try {
      const models = [];

      for await (const model of this.models.find()) {
        models.push({
          id: model.id,
          modelName: model.model_name
        });
      }

      return models;
    } catch (e) {
      console.error(e);
      return Promise.reject();
    }
  };

  createModel = async (modelID, modelName) => {
    const datetime = new Date();
    this.models.insertOne({
      ref_id: modelID,
      model_name: modelName,
      created: datetime,
      modified: datetime,
      _cls: "Model"
    });
  };

  createRunFromModel = async (modelID) => {
    let runID = uuidv1();
    let model = await this.models.findOne({ ref_id: modelID });
    let job = "alfalfa_worker.jobs.openstudio.CreateRun";
    if (model.model_name.endsWith(".fmu")) {
      job = "alfalfa_worker.jobs.modelica.CreateRun";
    }

    const params = {
      MessageBody: `{
        "job": "${job}",
        "params": {
          "model_id": "${modelID}",
          "run_id": "${runID}"
        }
      }`,
      QueueUrl: process.env.JOB_QUEUE_URL,
      MessageGroupId: "Alfalfa"
    };

    this.sqs.sendMessage(params, (err, data) => {
      if (err) {
        console.error(err);
      }
    });

    return runID;
  };

  setAlias = async (aliasName, refId) => {
    await this.aliases.updateOne({ name: aliasName }, { $set: { name: aliasName, ref_id: refId } }, { upsert: true });
  };

  getAlias = async (aliasName) => {
    const alias = await this.aliases.findOne({ name: aliasName });
    return alias ? alias.ref_id : null;
  };

  getAliases = async () => {
    const docs = {};
    const cursor = this.aliases.find();
    for await (const doc of cursor) {
      if (doc) docs[doc.name] = doc.ref_id;
    }
    return docs;
  };
}

module.exports = AlfalfaAPI;
