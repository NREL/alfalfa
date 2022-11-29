import AWS from "aws-sdk";
import got from "got";
import path from "path";
import { v1 as uuidv1 } from "uuid";
import dbops from "./dbops";
import { getHash, scan } from "./utils";

AWS.config.update({ region: process.env.REGION || "us-east-1" });
const sqs = new AWS.SQS();
const s3client = new AWS.S3({ endpoint: process.env.S3_URL });

function addSiteResolver(modelName, uploadID) {
  let run_id = uuidv1();
  let job = "alfalfa_worker.jobs.openstudio.CreateRun";
  if (modelName.endsWith(".fmu")) {
    job = "alfalfa_worker.jobs.modelica.CreateRun";
  }
  const params = {
    MessageBody: `{
      "job": "${job}",
      "params": {
        "model_name": "${modelName}",
        "upload_id": "${uploadID}",
        "run_id": "${run_id}"
      }
    }`,
    QueueUrl: process.env.JOB_QUEUE_URL,
    MessageGroupId: "Alfalfa"
  };

  sqs.sendMessage(params, (err, data) => {
    if (err) {
      console.error(err);
    }
  });

  return run_id;
}

function runSimResolver(modelName, uploadID) {
  let job = "alfalfa_worker.jobs.openstudio.AnnualRun";
  if (modelName.endsWith(".fmu")) {
    job = "alfalfa_worker.jobs.modelica.AnnualRun";
  }
  const params = {
    MessageBody: `{
      "job": "${job}",
      "params": {
        "model_name": "${modelName}",
        "upload_id": "${uploadID}"
      }
    }`,
    QueueUrl: process.env.JOB_QUEUE_URL,
    MessageGroupId: "Alfalfa"
  };

  sqs.sendMessage(params, (err, data) => {
    if (err) {
      console.error(err);
    } else {
      const simCollection = context.db.collection("simulation");
      simCollection.insert({
        _id: uploadID,
        ref_id: uploadID,
        siteRef: uploadID,
        simStatus: "Queued",
        name: path.parse(modelName).name.replace(".tar", "")
      });
    }
  });
}

function runSiteResolver(args, context) {
  //args: {
  //  siteRef : { type: new GraphQLNonNull(GraphQLString) },
  //  startDatetime : { type: GraphQLString },
  //  endDatetime : { type: GraphQLString },
  //  timescale : { type: GraphQLFloat },
  //  realtime : { type: GraphQLBoolean },
  //  externalClock : { type: GraphQLBoolean },
  //},
  const runs = context.db.collection("run");
  runs.findOne({ ref_id: args.siteRef }).then((doc) => {
    let job = "alfalfa_worker.jobs.openstudio.StepRun";
    if (doc.sim_type === "MODELICA") {
      job = "alfalfa_worker.jobs.modelica.StepRun";
    }
    const params = {
      MessageBody: `{
        "job": "${job}",
        "params": {
          "run_id": "${args.siteRef}",
          "timescale": "${args.timescale || 5}",
          "start_datetime": "${args.startDatetime}",
          "end_datetime": "${args.endDatetime}",
          "realtime": "${!!args.realtime}",
          "external_clock": "${!!args.externalClock}"
        }
      }`,
      QueueUrl: process.env.JOB_QUEUE_URL,
      MessageGroupId: "Alfalfa"
    };
    sqs.sendMessage(params, (err, data) => {
      if (err) {
        console.error(err);
      }
    });
  });
}

function invokeAction(action, siteRef) {
  return got
    .post("http://localhost/haystack/invokeAction", {
      headers: {
        Accept: "application/json"
      },
      json: {
        meta: {
          ver: "2.0",
          id: `r:${siteRef}`,
          action: `s:${action}`
        },
        cols: [
          {
            name: "empty" // At least one column is required
          }
        ],
        rows: []
      },
      responseType: "json"
    })
    .then(({ body }) => body);
}

function stopSiteResolver(args, context) {
  //args: {
  //  siteRef : { type: new GraphQLNonNull(GraphQLString) },
  //},
  return invokeAction("stopSite", args.siteRef);
}

function removeSiteResolver(args) {
  //args: {
  //  siteRef : { type: new GraphQLNonNull(GraphQLString) },
  //},
  return invokeAction("removeSite", args.siteRef);
}

function simsResolver(user, args, context) {
  return new Promise((resolve, reject) => {
    const sims = [];
    const simCollection = context.db.collection("simulation");
    simCollection
      .find(args)
      .toArray()
      .then((array) => {
        array.forEach((sim) => {
          sims.push({
            id: sim._id.toString(),
            siteRef: sim.ref_id,
            simStatus: sim.sim_status,
            s3Key: sim.s3_key,
            name: sim.name,
            url: sim.s3_key
              ? s3client.getSignedUrl("getObject", { Bucket: process.env.S3_BUCKET, Key: sim.s3_key, Expires: 86400 })
              : undefined,
            timeCompleted: sim.modified.toISOString(),
            results: JSON.stringify(sim.results)
          });
        });
        resolve(sims);
      })
      .catch((err) => {
        reject(err);
      });
  });
}

function runResolver(user, run_id, context) {
  return context.db
    .collection("run")
    .findOne({ ref_id: run_id })
    .then(async (doc) => {
      let sim_time = "";
      const site_hash = await getHash(context.redis, run_id);
      if (site_hash["sim_time"]) {
        sim_time = site_hash["sim_time"];
      }
      return {
        id: run_id,
        sim_type: doc.sim_type,
        status: doc.status,
        created: doc.created,
        modified: doc.modified,
        sim_time,
        error_log: doc.error_log
      };
    });
}

async function sitesResolver(user, siteRef, context) {
  const runs = {};

  if (siteRef) {
    const doc = await context.db.collection("run").findOne({ ref_id: siteRef });
    if (doc) runs[doc.ref_id] = doc;
  } else {
    const cursor = context.db.collection("run").find();
    for await (const doc of cursor) {
      if (doc) runs[doc.ref_id] = doc;
    }
  }

  return got
    .post("http://localhost/haystack/read", {
      headers: {
        Accept: "application/json"
      },
      json: {
        meta: {
          ver: "2.0"
        },
        cols: [
          {
            name: "filter"
          }
        ],
        rows: [
          {
            filter: `s:site${siteRef ? " and id==@" + siteRef : ""}`
          }
        ]
      },
      responseType: "json"
    })
    .then(({ body }) => {
      return body.rows.map(async (row) => {
        const site = {
          name: row.dis.replace(/^[a-z]:/, ""),
          siteRef: row.id.replace(/^[a-z]:/, ""),
          simStatus: row.simStatus.replace(/^[a-z]:/, ""),
          simType: row.simType.replace(/^[a-z]:/, ""),
          datetime: ""
        };
        const site_hash = await getHash(context.redis, site.siteRef);
        if (site_hash["sim_time"]) {
          site.datetime = site_hash["sim_time"];
        }
        if (site.siteRef in runs) {
          site.simStatus = runs[site.siteRef].status;
        }
        const { step } = row;
        if (step) {
          site.step = step.replace(/^[a-z]:/, "");
        }

        return site;
      });
    });
}

function sitePointResolver(siteRef, args, context) {
  return new Promise(async (resolve, reject) => {
    const pointKeys = await scan(context.redis, `site:${siteRef}:rec:*`);
    const currentValues = {};
    for (const key of pointKeys) {
      const [, pointId] = key.match(new RegExp(`^site:${siteRef}:rec:(.+)$`));
      currentValues[pointId] = await getHash(context.redis, key);
    }

    const recs = context.db.collection("recs");
    let query = { "rec.siteRef": `r:${siteRef}`, "rec.point": "m:" };
    if (args.writable) {
      query["rec.writable"] = "m:";
    }
    if (args.cur) {
      query["rec.cur"] = "m:";
    }
    recs
      .find(query)
      .toArray()
      .then((array) => {
        const points = [];
        array.map((rec) => {
          const point = {
            dis: rec.rec.dis,
            tags: []
          };
          for (const [key, value] of Object.entries({ ...rec.rec, ...currentValues[rec.ref_id] })) {
            point.tags.push({ key, value });
          }
          points.push(point);
        });
        resolve(points);
      })
      .catch((err) => {
        reject(err);
      });
  });
}

function advanceResolver(advancer, siteRef) {
  return advancer.advance(siteRef);
}

function writePointResolver(context, siteRef, pointName, value, level) {
  return dbops
    .getPoint(siteRef, pointName, context.db)
    .then((point) => {
      if (!point) {
        return Promise.reject(`Point '${pointName}' belonging to siteRef '${siteRef}' could not be found`);
      }

      return dbops.writePoint(point.ref_id, siteRef, level, value, context.db, context.redis);
    })
    .then((array) => JSON.stringify(array));
}

module.exports = {
  addSiteResolver,
  advanceResolver,
  removeSiteResolver,
  runResolver,
  runSimResolver,
  runSiteResolver,
  simsResolver,
  sitePointResolver,
  sitesResolver,
  stopSiteResolver,
  writePointResolver
};
