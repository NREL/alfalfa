import { Router } from "express";
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";
import { make, regex } from "simple-body-validator";
import { version } from "../package.json";
import AlfalfaAPI from "./api";
import { v1 as uuidv1 } from "uuid";

let api, db, redis;
const router = Router();
const route = "/api/v2";

const apiv2 = ({ db: _db, redis: _redis }) => {
  db = _db;
  redis = _redis;
  api = new AlfalfaAPI(db, redis);
  return router;
};

router.get("/", (req, res) => {
  res.redirect(301, "/docs");
});

// Remove trailing slashes
router.get(/\/$/, (req, res) => {
  res.redirect(301, `${route}${req.url.slice(0, -1)}`);
});

/**
 * @openapi
 * /sites:
 *   get:
 *     description: Return all sites
 *     operationId: sites
 *     tags:
 *       - Alfalfa
 *     responses:
 *       200:
 *         description: sites response
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 data:
 *                   type: array
 *                   items:
 *                     $ref: '#/components/schemas/Site'
 *             example:
 *               data:
 *                 - id: 4b8c6b40-f818-11ec-a8bd-75570e3e3a28
 *                   name: Building 1
 *                   uploadTimestamp: 2022-06-30 01:59:42.100453+00:00
 *                   uploadPath: uploads/4b8c6b40-f818-11ec-a8bd-75570e3e3a28/refrig_case_osw.zip
 *                 - id: 82ae8d50-f837-11ec-bda1-355419177ef9
 *                   name: Building 2
 *                   uploadTimestamp: 2022-06-30 05:43:06.884923+00:00
 *                   uploadPath: uploads/82ae8d50-f837-11ec-bda1-355419177ef9/refrig_case_osw_2.zip
 */
router.get("/sites", async (req, res) => {
  api
    .listSites()
    .then((data) => res.json({ data }))
    .catch(() => res.sendStatus(500));
});

/**
 * @openapi
 * /sites/{siteId}:
 *   get:
 *     description: Find a site by id
 *     operationId: site
 *     tags:
 *       - Alfalfa
 *     responses:
 *       200:
 *         description: site response
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 data:
 *                   $ref: '#/components/schemas/Site'
 *             example:
 *               data:
 *                 id: 4b8c6b40-f818-11ec-a8bd-75570e3e3a28
 *                 name: Building 1
 *                 uploadTimestamp: 2022-06-30 01:59:42.100453+00:00
 *                 uploadPath: uploads/4b8c6b40-f818-11ec-a8bd-75570e3e3a28/refrig_case_osw.zip
 *       404:
 *         description: site with ID does not exist
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Error'
 *             example:
 *               error: Site with id '12345' does not exist
 */
router.get("/sites/:id", async (req, res) => {
  const { id: siteId } = req.params;

  api
    .findSite(siteId)
    .then((data) => {
      if (data) {
        return res.json({ data });
      } else {
        return res.status(404).json({ error: `Site with id '${siteId}' does not exist` });
      }
    })
    .catch(() => res.sendStatus(500));
});

router.get("/sites/:id/time", async (req, res) => {
  const { id: siteId } = req.params;

  api
    .getSiteTime(siteId)
    .then((time) => res.json({ time }))
    .catch(() => res.sendStatus(500));
});

router.get("/sites/:id/points", (req, res) => {
  const { id: siteId } = req.params;
  api
    .listPoints(siteId, undefined, true)
    .then((data) => res.json({ data }))
    .catch(() => res.sendStatus(500));
});

router.get("/sites/:id/points/inputs", (req, res) => {
  const { id: siteId } = req.params;
  api
    .listPoints(siteId, /(INPUT)|(BIDIRECTIONAL)/)
    .then((data) => res.json({ data }))
    .catch(() => res.sendStatus(500));
});

router.get("/sites/:id/points/outputs", (req, res) => {
  const { id: siteId } = req.params;
  api
    .listPoints(siteId, /(OUTPUT)|(BIDIRECTIONAL)/, true)
    .then((data) => res.json({ data }))
    .catch(() => res.sendStatus(500));
});
router.put("/sites/:id/points/inputs", async (req, res) => {
  const { id: siteId } = req.params;
  const { points: writePoints } = req.body;

  try {
    for (const point of writePoints) {
      if (point.name) {
        point.id = await api.pointIdFromName(siteId, point.name);
      }
      await api.writeInputPoint(siteId, point.id, point.value);
    }
    res.sendStatus(204);
  } catch (e) {
    console.error(e);
    res.sendStatus(500);
  }
});

router.put("/sites/:id/points/:pointId", (req, res) => {
  const { id: siteId, pointId: pointId } = req.params;
  const { value: value } = req.body;
  api
    .writeInputPoint(siteId, pointId, value)
    .then(() => res.sendStatus(204))
    .catch(() => res.sendStatus(500));
});

/**
 * @openapi
 * /sites/{siteId}:
 *   delete:
 *     description: Delete a site by id
 *     operationId: deleteSite
 *     tags:
 *       - Alfalfa
 *     responses:
 *       204:
 *         description: the site was deleted successfully
 */
router.delete("/sites/:id", (req, res) => {
  const { id: siteId } = req.params;

  api
    .removeSite(siteId)
    .then(() => res.sendStatus(204))
    .catch(() => res.sendStatus(500));
});

/**
 * @openapi
 * /sites/{siteId}/start:
 *   post:
 *     description: Start a site run
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
 *                 description: The site will only advance when explicitly told to via an external call
 *                 example: false
 *               realtime:
 *                 type: boolean
 *                 description: The site will advance at 1x speed
 *                 example: false
 *             required:
 *               - startDatetime
 *               - endDatetime
 *     responses:
 *       204:
 *         description: the run was started successfully
 */
router.post("/sites/:id/start", async (req, res) => {
  const { id: siteId } = req.params;
  const { body: data } = req;

  const rules = {
    startDatetime: ["required", regex(/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/)],
    endDatetime: ["required", regex(/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/)],
    timescale: "strict|numeric|min:1",
    realtime: "strict|boolean",
    externalClock: "strict|boolean"
  };

  const validator = make(data, rules);
  if (!validator.stopOnFirstFailure().validate()) {
    return res.status(400).json({
      error: validator.errors().first()
    });
  }

  if (!(data.timescale || data.realtime || data.externalClock)) {
    return res.status(400).json({
      error: "At least one of timescale, realtime, or externalClock must be specified."
    });
  }

  if (data.realtime && data.externalClock) {
    return res.status(400).json({
      error: "Realtime and externalClock cannot both be enabled."
    });
  }

  api
    .startRun(siteId, data)
    .then((data) => {
      if (data?.error) {
        return res.status(400).json(data);
      } else {
        return res.sendStatus(204);
      }
    })
    .catch(() => {
      return res.sendStatus(500);
    });
});

/**
 * @openapi
 * /sites/{siteId}/advance:
 *   post:
 *     description: Advances a site run
 *     operationId: advanceRun
 *     tags:
 *       - Alfalfa
 *     responses:
 *       204:
 *         description: the run was advanced successfully
 */
router.post("/sites/:id/advance", (req, res) => {
  const { id: siteId } = req.params;

  api
    .advanceRun(siteId)
    .then(() => res.sendStatus(204))
    .catch(() => res.sendStatus(500));
});

/**
 * @openapi
 * /sites/{siteId}/stop:
 *   post:
 *     description: Stop a site run
 *     operationId: stopRun
 *     tags:
 *       - Alfalfa
 *     responses:
 *       204:
 *         description: the run was stopped successfully
 */
router.post("/sites/:id/stop", (req, res) => {
  const { id: siteId } = req.params;

  api
    .stopRun(siteId)
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
 *     description: Return the Alfalfa version and git SHA
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
 *                 sha:
 *                   type: string
 *             example:
 *               version: 0.4.0
 *               sha: c90d0641cb
 */
router.get("/version", (req, res) => {
  let sha = {};
  const shaPath = path.resolve(__dirname, "./sha.json");
  if (existsSync(shaPath)) {
    sha = JSON.parse(readFileSync(shaPath, "utf-8"));
  }
  res.json({ version, ...sha });
});

router.get("/models", async (req, res) => {
  api
    .listModels()
    .then((data) => res.json({ data }))
    .catch(() => res.sendStatus(500));
});

router.post("/models/:id/createRun", (req, res) => {
  const { id: modelID } = req.params;
  api
    .createRunFromModel(modelID)
    .then((runID) => {
      res.json({ runID: runID });
    })
    .catch((err) => {
      console.log(err);
      res.sendStatus(500);
    });
});

// Create a post url for file uploads
// from a browser
router.post("/models/upload", (req, res) => {
  const { modelName } = req.body;
  const modelID = uuidv1();
  const modelPath = `uploads/${modelID}/${modelName}`;

  api.createModel(modelID, modelName);

  // Construct a new postPolicy.
  const params = {
    Bucket: process.env.S3_BUCKET,
    Fields: {
      key: modelPath
    }
  };

  api.s3.createPresignedPost(params, function (err, data) {
    if (err) {
      throw err;
    } else {
      // if you're running locally and using internal Docker networking ( "http://minio:9000")
      // as your S3_URL, you need to specify an alternate S3_URL_EXTERNAL to POST to, ie "http://localhost:9000"
      if (process.env.S3_URL_EXTERNAL) {
        data.url = `${process.env.S3_URL_EXTERNAL}/${process.env.S3_BUCKET}`;
      } else {
        data.url = `${process.env.S3_URL}/${process.env.S3_BUCKET}`;
      }
      data.modelID = modelID;
      res.json(data);
    }
  });
});

router.get("*", (req, res) => {
  res.sendStatus(404);
});

export default apiv2;
