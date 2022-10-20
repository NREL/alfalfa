import AWS from "aws-sdk";
import { Router } from "express";
import got from "got";
import { make, regex } from "simple-body-validator";
import { version } from "../package.json";

AWS.config.update({ region: process.env.REGION || "us-east-1" });
const sqs = new AWS.SQS();

let db;
const router = Router();

const api = ({ db: _db }) => {
  db = _db;
  return router;
};

router.get("/", (req, res) => {
  res.redirect(301, "/docs");
});

function mapHaystack(row) {
  return Object.keys(row).reduce((result, key) => {
    result[key] = row[key].replace(/^[a-z]:/, "");
    return result;
  }, {});
}

/**
 * @openapi
 * /models:
 *   get:
 *     description: Return all models
 *     operationId: models
 *     tags:
 *       - Alfalfa
 *     responses:
 *       200:
 *         description: models response
 *         content:
 *           application/json:
 *             schema:
 *               type: array
 *               items:
 *                 $ref: '#/components/schemas/Model'
 *             example:
 *               data:
 *                 - id: 4b8c6b40-f818-11ec-a8bd-75570e3e3a28
 *                   description: Building 1
 *                   uploadTimestamp: '2022-06-30 01:59:42.100453+00:00'
 *                   uploadPath: uploads/4b8c6b40-f818-11ec-a8bd-75570e3e3a28/refrig_case_osw.zip
 *                 - id: 82ae8d50-f837-11ec-bda1-355419177ef9
 *                   description: Building 2
 *                   uploadTimestamp: '2022-06-30 05:43:06.884923+00:00'
 *                   uploadPath: uploads/82ae8d50-f837-11ec-bda1-355419177ef9/refrig_case_osw_2.zip
 */
router.get("/models", async (req, res) => {
  const docs = {};
  const cursor = db.collection("run").find();
  for await (const doc of cursor) {
    if (doc) docs[doc.ref_id] = doc;
  }

  got
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
            filter: "s:site"
          }
        ]
      },
      responseType: "json"
    })
    .then(({ body }) => {
      const models = body.rows.map((row) => {
        const { id, dis: description } = mapHaystack(row);
        const model = {
          id,
          description
        };

        const doc = docs[id];
        if (doc) {
          model.uploadTimestamp = doc.created;
          model.uploadPath = doc.model;
        }

        return model;
      });
      res.json({ data: models });
    })
    .catch(() => res.sendStatus(500));
});

/**
 * @openapi
 * /models/{modelId}:
 *   get:
 *     description: Find a model by id
 *     operationId: model
 *     tags:
 *       - Alfalfa
 *     responses:
 *       200:
 *         description: model response
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Model'
 *             example:
 *               data:
 *                 id: 4b8c6b40-f818-11ec-a8bd-75570e3e3a28
 *                 description: Building 1
 *                 uploadTimestamp: '2022-06-30 01:59:42.100453+00:00'
 *                 uploadPath: uploads/4b8c6b40-f818-11ec-a8bd-75570e3e3a28/refrig_case_osw.zip
 *       400:
 *         description: invalid ID supplied
 */
router.get("/models/:id", async (req, res) => {
  const { id: modelId } = req.params;
  const doc = await db.collection("run").findOne({ ref_id: modelId });

  got
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
            filter: `s:site and id==@${modelId}`
          }
        ]
      },
      responseType: "json"
    })
    .then(({ body }) => {
      if (body.rows.length === 0) {
        res.sendStatus(400);
        return;
      }

      const { id, dis: description } = mapHaystack(body.rows[0]);
      const model = {
        id,
        description
      };

      if (doc) {
        model.uploadTimestamp = doc.created;
        model.uploadPath = doc.model;
      }

      res.json({ data: model });
    })
    .catch(() => res.sendStatus(500));
});

/**
 * @openapi
 * /models/{modelId}:
 *   delete:
 *     description: Delete a model by id
 *     operationId: deleteModel
 *     tags:
 *       - Alfalfa
 *     responses:
 *       204:
 *         description: the model was deleted successfully
 */
router.delete("/models/:id", (req, res) => {
  const { id: modelId } = req.params;

  got
    .post("http://localhost/haystack/invokeAction", {
      headers: {
        Accept: "application/json"
      },
      json: {
        meta: {
          ver: "2.0",
          id: `r:${modelId}`,
          action: "s:removeSite"
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
    .then(() => res.sendStatus(204))
    .catch(() => res.sendStatus(500));
});

/**
 * @openapi
 * /models/{modelId}/start:
 *   post:
 *     description: Start a model run
 *     operationId: startRun
 *     tags:
 *       - Alfalfa
 *     requestBody:
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               startDatetime:
 *                 type: string
 *                 description: EnergyPlus Start Time
 *                 example: 2022-06-30 12:00:00
 *               endDatetime:
 *                 type: string
 *                 description: EnergyPlus End Time
 *                 example: 2022-06-30 12:10:00
 *               timescale:
 *                 type: number
 *                 description: Time multiplier determining simulation speed
 *                 example: 5
 *               externalClock:
 *                 type: boolean
 *                 description: The model will only advance when explicitly told to via an external call
 *                 example: false
 *               realtime:
 *                 type: boolean
 *                 description: The model will advance at 1x speed
 *                 example: false
 *             required:
 *               - startDatetime
 *               - endDatetime
 *     responses:
 *       204:
 *         description: the run was started successfully
 */
router.post("/models/:id/start", async (req, res) => {
  const { id: modelId } = req.params;
  const { body } = req;

  const rules = {
    startDatetime: ["required", regex(/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/)],
    endDatetime: ["required", regex(/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/)],
    timescale: "strict|numeric|min:1",
    realtime: "strict|boolean",
    externalClock: "strict|boolean"
  };

  const validator = make(body, rules);
  if (!validator.stopOnFirstFailure().validate()) {
    return res.status(400).json({
      error: validator.errors().first()
    });
  }

  if (!(body.timescale || body.realtime || body.externalClock)) {
    return res.status(400).json({
      error: "At least one of timescale, realtime, or externalClock must be specified."
    });
  }

  if (body.realtime && body.externalClock) {
    return res.status(400).json({
      error: "Realtime and externalClock cannot both be enabled."
    });
  }

  const { sim_type } = await db.collection("run").findOne({ ref_id: modelId });
  const { startDatetime, endDatetime, timescale, realtime, externalClock } = body;
  const params = {
    MessageBody: `{
      "job": "alfalfa_worker.jobs.${sim_type === "MODELICA" ? "modelica" : "openstudio"}.StepRun",
      "params": {
        "run_id": "${modelId}",
        "start_datetime": "${startDatetime}",
        "end_datetime": "${endDatetime}",
        "timescale": "${timescale || 5}",
        "realtime": "${!!realtime}",
        "external_clock": "${!!externalClock}"
      }
    }`,
    QueueUrl: process.env.JOB_QUEUE_URL,
    MessageGroupId: "Alfalfa"
  };
  sqs.sendMessage(params, (err, data) => {
    if (err) {
      return res.sendStatus(500);
    }
    res.sendStatus(204);
  });
});

/**
 * @openapi
 * /models/{modelId}/stop:
 *   post:
 *     description: Stop a model run
 *     operationId: stopRun
 *     tags:
 *       - Alfalfa
 *     responses:
 *       204:
 *         description: the run was stopped successfully
 */
router.post("/models/:id/stop", (req, res) => {
  const { id: modelId } = req.params;

  got
    .post("http://localhost/haystack/invokeAction", {
      headers: {
        Accept: "application/json"
      },
      json: {
        meta: {
          ver: "2.0",
          id: `r:${modelId}`,
          action: "s:stopSite"
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
    .then(() => res.sendStatus(204))
    .catch(() => res.sendStatus(500));
});

/**
 * @openapi
 * /aliases
 *   get:
 *     description: Return list of aliases
 *     operationId: aliases
 *     tags:
 *       - Alfalfa
 *     responses:
 *       200:
 *         description: aliases response
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *             example:
 *               foo: d4e2c041-0389-4933-8aa4-016d80283779
 *               bar: 9e2acb8e-974e-406b-a990-48e9743b01de
 */
router.get("/aliases", async (req, res) => {
  const docs = {};
  const cursor = db.collection("alias").find();
  for await (const doc of cursor) {
    if (doc) docs[doc.name] = doc.ref_id;
  }
  res.json(docs);
});

router.get("/aliases/:name", async (req, res) => {
  const { name: alias_name } = req.params;
  const alias = await db.collection("alias").findOne({ name: alias_name });
  console.log(alias);
  if (alias) {
    res.json(alias);
  } else {
    res.sendStatus(404);
  }
});

router.put("/aliases/:name", async (req, res) => {
  const { name: alias_name } = req.params;
  const { body } = req;

  db.collection("alias").updateOne(
    { name: alias_name },
    { $set: { name: alias_name, ref_id: body.ref_id } },
    { upsert: true }
  );
  res.sendStatus(200);
});

/**
 * @openapi
 * /version:
 *   get:
 *     description: Return the Alfalfa version
 *     operationId: version
 *     tags:
 *       - Alfalfa
 *     responses:
 *       200:
 *         description: version response
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 version:
 *                   type: string
 *             example:
 *               version: 0.3.0
 */
router.get("/version", (req, res) => {
  res.json({ version });
});

router.get("*", (req, res) => {
  res.sendStatus(404);
});

export default api;
