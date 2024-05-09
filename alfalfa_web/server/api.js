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
    this.aliases = db.collection("alias");

    this.redis = redis;
    this.pub = redis.duplicate();
    this.pub.connect();

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

  listRuns = async () => {
    const formattedRuns = await Promise.all(
      await this.getRuns().then(async (runs) => {
        return runs.map(this.formatRun);
      })
    );
    return formattedRuns;
  };

  getRuns = async () => {
    const runsCursor = this.runs.find();
    return runsCursor.toArray();
  };

  getRunById = async (runId) => {
    const run = this.runs.findOne({ ref_id: runId });
    return Promise.resolve(run);
  };

  getRun = async (runObjectId) => {
    return this.runs.findOne({ _id: runObjectId });
  };

  formatRun = async (run) => {
    const run_dict = {
      id: run.ref_id,
      name: run.name,
      status: run.status,
      datetime: await this.getRunTime(run),
      simType: run.sim_type,
      uploadTimestamp: run.created,
      errorLog: run.error_log
    };
    const model = await this.models.findOne({ _id: run.model });
    if (model) {
      run_dict.uploadPath = `uploads/${model.ref_id}/${model.model_name}`;
    }
    return run_dict;
  };

  getRunDownloadPath = async (run) => {
    const signedURL = await getSignedUrl(
      this.s3,
      new GetObjectCommand({
        Bucket: process.env.S3_BUCKET,
        Key: `run/${run.ref_id}.tar.gz`,
        ResponseContentDisposition: `attachment; filename="${run.ref_id}.tar.gz"`
      }),
      {
        expiresIn: 86400
      }
    );
    return signedURL;
  };

  getRunTime = async (run) => {
    return await getHashValue(this.redis, run.ref_id, "sim_time");
  };

  getPointsByRun = async (run) => {
    const pointsCursor = this.points.find({ run: run._id });
    return Promise.resolve(pointsCursor.toArray());
  };

  getPointsById = async (run, pointIds) => {
    return Promise.all(
      pointIds.map((pointId) => {
        return this.getPointById(run, pointId);
      })
    );
  };

  getPointsByType = async (run, pointTypes) => {
    const query = {};
    query.run = run._id;
    query.point_type = new RegExp(`^${pointTypes.join("|")}$`);

    const pointsCursor = this.points.find(query);
    return Promise.resolve(pointsCursor.toArray());
  };

  getPointById = async (run, pointId) => {
    const point = this.points.findOne({ ref_id: pointId, run: run._id });
    if (point == null) {
      return Promise.reject(`Point with id '${pointId}' does not exist`);
    }
    return Promise.resolve(point);
  };

  formatPoint = (point) => {
    const pointDict = {
      id: point.ref_id,
      name: point.name,
      type: point.point_type
    };
    return pointDict;
  };

  validatePointWrite = async (point, value) => {
    // Check point type
    if (point.point_type == "OUTPUT") {
      return Promise.reject(`Point with id '${point.ref_id}' is an 'OUTPUT' and can not be written to`);
    }

    // @TODO: when point datatype is added this will need to be adjusted
    if (typeof value !== "number" && value !== null) {
      return Promise.reject(
        `Point with id '${point.ref_id}' cannot be written to by value '${value}' of type ${typeof value}`
      );
    }

    return Promise.resolve(true);
  };

  readOutputPoint = async (run, point) => {
    const key = `${getPointKey(run.ref_id, point.ref_id)}:out`;
    const value = await getHashValue(this.redis, key, "curVal");
    if (value !== null) {
      return parseFloat(value.replace(/^[a-z]:/, ""));
    }
    return null;
  };

  writeInputPoint = async (run, point, value) => {
    if (point.point_type === "OUTPUT") {
      return Promise.reject("Cannot write to an Output point");
    }

    if (value == null) {
      value = "null";
    }
    return writePoint(point.ref_id, run.ref_id, 1, value, this.db, this.redis);
  };

  removeRun = async (run) => {
    // Delete run
    const { deletedCount } = await this.runs.deleteOne({ _id: run._id });

    if (deletedCount == 1) {
      // Delete points
      await this.points.deleteMany({ run: run._id });

      // Delete aliases
      await this.aliases.deleteMany({ run: run._id });

      // Delete redis keys
      const keys = await scan(this.redis, `run:${run.ref_id}*`);
      if (keys.length) await del(this.redis, keys);
      const key = await scan(this.redis, run.ref_id);
      if (key.length) await del(this.redis, key);

      return Promise.resolve();
    } else {
      return Promise.reject("Could not remove Run");
    }
  };

  startRun = async (run, data) => {
    const { sim_type, status } = run;

    if (status !== "READY") return { error: "Run is not in 'READY' state" };

    const { startDatetime, endDatetime, timescale, realtime, externalClock } = data;

    const messageBody = {
      job: `alfalfa_worker.jobs.${sim_type === "MODELICA" ? "modelica" : "openstudio"}.StepRun`,
      params: {
        run_id: run.ref_id,
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
  };

  advanceRun = async (run) => {
    return await this.sendRunMessage(run, "advance");
  };

  stopRun = async (run) => {
    return await this.sendRunMessage(run, "stop");
  };

  sendRunMessage = (run, method, data = null, timeout = 60000, pollingInterval = 100) => {
    return new Promise(async (resolve, reject) => {
      const message_id = uuidv1();
      await this.pub.publish(run.ref_id, JSON.stringify({ message_id, method, data }));
      const send_time = Date.now();

      let interval;

      const finalize = (success, message = "") => {
        clearInterval(interval);
        if (success) {
          resolve({ message });
        } else {
          reject({ message });
        }
      };

      interval = setInterval(async () => {
        if (Date.now() - timeout > send_time) {
          finalize(false, "no simulation reply");
        }
        const response = await getHashValue(this.redis, run.ref_id, message_id);
        if (!response) return;
        finalize(JSON.parse(response).status === "ok", response);
      }, pollingInterval);
    });
  };

  listModels = async () => {
    const models = await this.getModels();
    return models.map(this.formatModel);
  };

  getModels = async () => {
    return this.models.find().toArray();
  };

  getModelById = async (modelId) => {
    return this.models.findOne({ ref_id: modelId });
  };

  formatModel = (model) => {
    const { ref_id: id, model_name: modelName, created, modified } = model;
    return {
      id,
      modelName,
      created,
      modified
    };
  };

  getModelDownloadPath = async (model) => {
    const signedURL = await getSignedUrl(
      this.s3,
      new GetObjectCommand({
        Bucket: process.env.S3_BUCKET,
        Key: `uploads/${model.ref_id}/${model.model_name}`,
        ResponseContentDisposition: `attachment; filename="${model.ref_id}.tar.gz"`
      }),
      {
        expiresIn: 86400
      }
    );
    return signedURL;
  };

  createModel = async (modelId, modelName) => {
    const datetime = new Date();
    await this.models.insertOne({
      ref_id: modelId,
      model_name: modelName,
      created: datetime,
      modified: datetime,
      _cls: "Model"
    });
  };

  createRunFromModel = async (model) => {
    const runId = uuidv1();
    const job = `alfalfa_worker.jobs.${model.model_name.endsWith(".fmu") ? "modelica" : "openstudio"}.CreateRun`;

    const messageBody = {
      job,
      params: {
        model_id: model.ref_id,
        run_id: runId
      }
    };

    await this.sqs.send(
      new SendMessageCommand({
        MessageBody: JSON.stringify(messageBody),
        QueueUrl: process.env.JOB_QUEUE_URL,
        MessageGroupId: "Alfalfa"
      })
    );

    return { runId };
  };

  setAlias = async (alias, run) => {
    return await this.aliases.updateOne({ name: alias }, { $set: { name: alias, run: run._id } }, { upsert: true });
  };

  getAliasByName = async (aliasName) => {
    return this.aliases.findOne({ name: aliasName });
  };

  listAliases = async () => {
    return (await this.aliases.find().toArray()).reduce((aliases, { name, run }) => {
      aliases[name] = this.runs.findOne({ _id: run }).ref_id;
      return aliases;
    }, {});
  };

  removeAlias = async (alias) => {
    const { deletedCount } = await this.aliases.deleteOne({ _id: alias._id });
    if (deletedCount == 1) {
      return Promise.resolve();
    } else {
      return Promise.reject("Could not remove Alias");
    }
  };

  createUploadPost = async (modelName) => {
    const modelId = uuidv1();
    const modelPath = `uploads/${modelId}/${modelName}`;

    await this.createModel(modelId, modelName);

    const presignedPost = await createPresignedPost(this.s3, {
      Bucket: process.env.S3_BUCKET,
      Key: modelPath
    });

    return {
      ...presignedPost,
      url: `${process.env.S3_URL_EXTERNAL || process.env.S3_URL}/${process.env.S3_BUCKET}`,
      modelId
    };
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
