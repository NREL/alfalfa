import { GetObjectCommand, S3Client } from "@aws-sdk/client-s3";
import { SendMessageCommand, SQSClient } from "@aws-sdk/client-sqs";
import { fromEnv } from "@aws-sdk/credential-providers";
import { createPresignedPost } from "@aws-sdk/s3-presigned-post";
import { getSignedUrl } from "@aws-sdk/s3-request-presigner";
import { DateTime } from "luxon";
import { v1 as uuidv1 } from "uuid";
import { writePoint } from "./dbops";
import { del, getHash, getHashValue, getPointKey, mapHaystack, reduceById, reduceByRefId, scan } from "./utils";

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

    const credentials = fromEnv();
    const region = process.env.REGION || "us-east-1";
    this.sqs = new SQSClient({
      credentials,
      endpoint: new URL(process.env.JOB_QUEUE_URL).origin,
      region
    });
    this.s3 = new S3Client({
      credentials,
      endpoint: process.env.S3_URL_EXTERNAL || process.env.S3_URL,
      forcePathStyle: true,
      region
    });
  }

  listSites = async () => {
    try {
      const runs = [];

      for await (const run of this.runs.find()) {
        const site = await this.findSite(run.ref_id);

        if (site) {
          runs.push(site);
        }
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
        let site = await this.sites.findOne({ ref_id: siteRef });

        const site_dict = {
          id: siteRef,
          name: model.model_name,
          status: run.status.toLowerCase(),
          datetime: "",
          simType: run.sim_type,
          uploadTimestamp: run.created,
          uploadPath: `uploads/${model.ref_id}/${model.model_name}`,
          errorLog: run.error_log
        };

        if (site) {
          const siteHash = await getHash(this.redis, siteRef);

          site_dict.name = site?.dis;
          site_dict.datetime = siteHash?.sim_time;
        }
        return site_dict;
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
      console.error(e);
      return Promise.reject();
    }
  };

  listPoints = async (siteRef, pointType, getValue = false) => {
    try {
      const points = [];
      const run = await this.runs.findOne({ ref_id: siteRef });
      if (run) {
        const query = { run: run._id };
        if (pointType) query.point_type = pointType;
        // const myPoints = await this.points.find(query).toArray()

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
    const key = `${getPointKey(siteRef, pointId)}:out`;
    const value = await getHashValue(this.redis, key, "curVal");
    if (value !== null) {
      return parseFloat(value.replace(/^[a-z]:/, ""));
    }
  };

  writeInputPoint = async (siteRef, pointId, value) => {
    const run = await this.runs.findOne({ ref_id: siteRef });
    const point = await this.points.findOne({ run: run._id, ref_id: pointId });

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

      if (site) {
        // Delete points
        for await (const run of this.runs.find({ ref_id: site.ref_id })) {
          await this.points.deleteMany({ run: run._id });
        }

        // Delete runs
        await this.runs.deleteMany({ ref_id: site.ref_id });

        // Delete recs
        await this.recs.deleteMany({ site: site._id });

        // Delete simulations
        await this.simulations.deleteMany({ site: site._id });

        // Delete aliases
        await this.aliases.deleteMany({ ref_id: site.ref_id });

        // Delete redis keys
        const keys = await scan(this.redis, `site:${siteRef}*`);
        if (keys.length) await del(this.redis, keys);
        const key = await scan(this.redis, siteRef);
        if (key.length) await del(this.redis, key);

        return true;
      }
    } catch (e) {
      console.error(e);
      return Promise.reject();
    }
  };

  startRun = async (siteRef, data) => {
    try {
      const { sim_type, status } = await this.runs.findOne({ ref_id: siteRef });

      if (status !== "READY") return { error: "Run is not in 'READY' state" };

      const { startDatetime, endDatetime, timescale, realtime, externalClock } = data;

      const messageBody = {
        job: `alfalfa_worker.jobs.${sim_type === "MODELICA" ? "modelica" : "openstudio"}.StepRun`,
        params: {
          run_id: siteRef,
          start_datetime: startDatetime,
          end_datetime: endDatetime,
          timescale: `${timescale || 5}`,
          realtime: `${!!realtime}`,
          external_clock: `${!!externalClock}`
        }
      };
      await this.sqs.send(
        new SendMessageCommand({
          MessageBody: JSON.stringify(messageBody),
          QueueUrl: process.env.JOB_QUEUE_URL,
          MessageGroupId: "Alfalfa"
        })
      );
    } catch (e) {
      console.error(e);
      return Promise.reject();
    }
  };

  advanceRun = async (siteRef) => {
    try {
      return await this.sendRunMessage(siteRef, "advance");
    } catch (e) {
      console.error(e);
      return Promise.reject();
    }
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
      return (await this.models.find().toArray()).map(({ ref_id: id, model_name: modelName, created, modified }) => ({
        id,
        modelName,
        created,
        modified
      }));
    } catch (e) {
      console.error(e);
      return Promise.reject();
    }
  };

  createModel = async (modelID, modelName) => {
    const datetime = new Date();
    await this.models.insertOne({
      ref_id: modelID,
      model_name: modelName,
      created: datetime,
      modified: datetime,
      _cls: "Model"
    });
  };

  createRunFromModel = async (modelID) => {
    try {
      const runID = uuidv1();
      const model = await this.models.findOne({ ref_id: modelID });
      if (model) {
        const job = `alfalfa_worker.jobs.${model.model_name.endsWith(".fmu") ? "modelica" : "openstudio"}.CreateRun`;

        const messageBody = {
          job,
          params: {
            model_id: modelID,
            run_id: runID
          }
        };

        await this.sqs.send(
          new SendMessageCommand({
            MessageBody: JSON.stringify(messageBody),
            QueueUrl: process.env.JOB_QUEUE_URL,
            MessageGroupId: "Alfalfa"
          })
        );

        return { runID };
      }
    } catch (e) {
      console.error(e);
      return Promise.reject();
    }
  };

  setAlias = async (alias, refId) => {
    try {
      const site = await this.sites.findOne({ ref_id: refId });
      if (site) {
        return await this.aliases.updateOne(
          { name: alias },
          { $set: { name: alias, ref_id: refId } },
          { upsert: true }
        );
      }
    } catch (e) {
      console.error(e);
      return Promise.reject();
    }
  };

  findAlias = async (aliasName) => {
    try {
      const alias = await this.aliases.findOne({ name: aliasName });
      if (alias) return alias.ref_id;
    } catch (e) {
      console.error(e);
      return Promise.reject();
    }
  };

  listAliases = async () => {
    try {
      return (await this.aliases.find().toArray()).reduce((aliases, { name, ref_id }) => {
        aliases[name] = ref_id;
        return aliases;
      }, {});
    } catch (e) {
      console.error(e);
      return Promise.reject();
    }
  };

  removeAlias = async (alias) => {
    try {
      const { deletedCount } = await this.aliases.deleteOne({ name: alias });
      return deletedCount;
    } catch (e) {
      console.error(e);
      return Promise.reject();
    }
  };

  createUploadPost = async (modelName) => {
    try {
      const modelID = uuidv1();
      const modelPath = `uploads/${modelID}/${modelName}`;

      await this.createModel(modelID, modelName);

      const presignedPost = await createPresignedPost(this.s3, {
        Bucket: process.env.S3_BUCKET,
        Key: modelPath
      });

      return {
        ...presignedPost,
        url: `${process.env.S3_URL_EXTERNAL || process.env.S3_URL}/${process.env.S3_BUCKET}`,
        modelID
      };
    } catch (e) {
      console.error(e);
      return Promise.reject();
    }
  };

  listSimulations = async () => {
    try {
      const sims = [];

      const simulations = await this.simulations.find().toArray();
      for (const {
        ref_id: id,
        name,
        time_completed: timeCompleted,
        sim_status: status,
        s3_key: key,
        results
      } of simulations) {
        const url = key
          ? await getSignedUrl(
              this.s3,
              new GetObjectCommand({
                Bucket: process.env.S3_BUCKET,
                Key: key,
                ResponseContentDisposition: `attachment; filename="${name}.tar.gz"`
              }),
              {
                expiresIn: 86400
              }
            )
          : undefined;

        sims.push({
          id,
          name,
          timeCompleted: DateTime.fromISO(timeCompleted.replace(" ", "T"), { zone: "UTC" }).toISO(),
          status: status.toLowerCase(),
          url,
          results
        });
      }

      return sims;
    } catch (e) {
      console.error(e);
      return Promise.reject();
    }
  };
}

module.exports = AlfalfaAPI;
