import { existsSync, readFileSync } from "node:fs";
import path from "node:path";
import { Router } from "express";
import { make, regex, register, setTranslationObject } from "simple-body-validator";
import { version } from "../package.json";

const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
register("uuid", (value) => uuid.test(value));
setTranslationObject({
  en: {
    uuid: "The :attribute uuid format is invalid."
  }
});

let api;
const router = Router();
const route = "/api/v2";

const apiv2 = ({ api: _api }) => {
  api = _api;
  return router;
};

const validate = (data, rules) => {
  const validator = make(data, rules);
  if (!validator.stopOnFirstFailure().validate()) {
    return validator.errors().first();
  }
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
 *     operationId: List sites
 *     description: Return list of sites
 *     tags:
 *       - Site
 *     responses:
 *       200:
 *         description: Sites response
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
 *                   status: complete
 *                   simType: osm
 *                   datetime: 2022-03-15 00:00:00
 *                   uploadTimestamp: 2022-03-15T14:55:27.131Z
 *                   uploadPath: uploads/6b3ddba0-c341-11ed-974b-bf90e67a18f9/refrig_case_osw.zip
 *                   errorLog: ''
 *                 - id: 82ae8d50-f837-11ec-bda1-355419177ef9
 *                   name: Building 2
 *                   status: ready
 *                   simType: osm
 *                   datetime: ''
 *                   uploadTimestamp: 2022-06-30T05:43:06.885Z
 *                   uploadPath: uploads/82ae8d50-f837-11ec-bda1-355419177ef9/refrig_case_osw_2.zip
 *                   errorLog: ''
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
 *     operationId: Get site
 *     description: Lookup a site by id
 *     tags:
 *       - Site
 *     responses:
 *       200:
 *         description: Site response
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
 *                 uploadTimestamp: 2022-06-30T05:43:06.885Z
 *                 uploadPath: uploads/4b8c6b40-f818-11ec-a8bd-75570e3e3a28/refrig_case_osw.zip
 *       404:
 *         description: Site ID does not exist
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Error'
 */
router.get("/sites/:siteId", async (req, res) => {
  const { siteId } = req.params;

  const error = validate(
    { siteId },
    {
      siteId: "required|uuid"
    }
  );
  if (error) return res.status(400).json({ error });

  api
    .findSite(siteId)
    .then((data) => {
      if (data) {
        return res.json({ data });
      } else {
        return res.status(404).json({
          error: `Site ID '${siteId}' does not exist`
        });
      }
    })
    .catch(() => res.sendStatus(500));
});

/**
 * @openapi
 * /sites/{siteId}/time:
 *   get:
 *     operationId: Get simulation time
 *     description: Return the current time of the simulation if it has been started
 *     tags:
 *       - Simulation
 *     responses:
 *       200:
 *         description: Time response
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 time:
 *                   type: string
 *             example:
 *               time: 2022-06-15 00:00:00
 */
router.get("/sites/:siteId/time", async (req, res) => {
  const { siteId } = req.params;

  const error = validate(
    { siteId },
    {
      siteId: "required|uuid"
    }
  );
  if (error) return res.status(400).json({ error });

  api
    .getSiteTime(siteId)
    .then((time) => res.json({ time }))
    .catch(() => res.sendStatus(500));
});

/**
 * @openapi
 * /sites/{siteId}/points:
 *   get:
 *     operationId: List points
 *     description: Return list of points for a site
 *     tags:
 *       - Site
 *     responses:
 *       200:
 *         description: Points response
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 data:
 *                   type: array
 *                   items:
 *                     $ref: '#/components/schemas/Point'
 *             example:
 *               data:
 *                 - id: c5bfacf7-bd44-4061-a44c-940bb71ba91f
 *                   name: CaseDefrostStatus
 *                   type: BIDIRECTIONAL
 *                   value: 0
 *                 - id: a26d37f8-b479-46d2-8b0f-7e686be22223
 *                   name: MasterEnable
 *                   type: INPUT
 *                 - id: 8ed24c59-858d-48e8-ac4b-24b7bb688797
 *                   name: Case Compressor Power 2
 *                   type: OUTPUT
 *                   value: 209.7981895033449
 *       404:
 *         description: Site ID does not exist
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Error'
 */
router.get("/sites/:siteId/points", (req, res) => {
  const { siteId } = req.params;

  const error = validate(
    { siteId },
    {
      siteId: "required|uuid"
    }
  );
  if (error) return res.status(400).json({ error });

  api
    .listPoints(siteId, undefined, true)
    .then((data) => {
      if (data) {
        return res.json({ data });
      } else {
        return res.status(404).json({
          error: `Site ID '${siteId}' does not exist`
        });
      }
    })
    .catch(() => res.sendStatus(500));
});

/**
 * @openapi
 * /sites/{siteId}/points/inputs:
 *   get:
 *     operationId: List input points
 *     description: Return list of input and bidirectional points for a site, bidirectional values are excluded
 *     tags:
 *       - Site
 *     responses:
 *       200:
 *         description: Points response
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 data:
 *                   type: array
 *                   items:
 *                     $ref: '#/components/schemas/Point'
 *             example:
 *               data:
 *                 - id: c5bfacf7-bd44-4061-a44c-940bb71ba91f
 *                   name: CaseDefrostStatus
 *                   type: BIDIRECTIONAL
 *                 - id: a26d37f8-b479-46d2-8b0f-7e686be22223
 *                   name: MasterEnable
 *                   type: INPUT
 */
router.get("/sites/:siteId/points/inputs", (req, res) => {
  const { siteId } = req.params;

  const error = validate(
    { siteId },
    {
      siteId: "required|uuid"
    }
  );
  if (error) return res.status(400).json({ error });

  api
    .listPoints(siteId, /^(INPUT|BIDIRECTIONAL)$/)
    .then((data) => res.json({ data }))
    .catch(() => res.sendStatus(500));
});

/**
 * @openapi
 * /sites/{siteId}/points/outputs:
 *   get:
 *     operationId: List output points
 *     description: Return list of output and bidirectional points for a site
 *     tags:
 *       - Site
 *     responses:
 *       200:
 *         description: Points response
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 data:
 *                   type: array
 *                   items:
 *                     $ref: '#/components/schemas/Point'
 *             example:
 *               data:
 *                 - id: c5bfacf7-bd44-4061-a44c-940bb71ba91f
 *                   name: CaseDefrostStatus
 *                   type: BIDIRECTIONAL
 *                   value: 0
 *                 - id: 8ed24c59-858d-48e8-ac4b-24b7bb688797
 *                   name: Case Compressor Power 2
 *                   type: OUTPUT
 *                   value: 209.7981895033449
 */
router.get("/sites/:siteId/points/outputs", (req, res) => {
  const { siteId } = req.params;

  const error = validate(
    { siteId },
    {
      siteId: "required|uuid"
    }
  );
  if (error) return res.status(400).json({ error });

  api
    .listPoints(siteId, /^(OUTPUT|BIDIRECTIONAL)$/, true)
    .then((data) => res.json({ data }))
    .catch(() => res.sendStatus(500));
});

/**
 * @openapi
 * /sites/{siteId}/points/inputs:
 *   put:
 *     operationId: Update input points
 *     description: Set the write array values for multiple input and bidirectional points for a site given point ids or names
 *     tags:
 *       - Site
 *     requestBody:
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               points:
 *                 type: array
 *                 items:
 *                   type: object
 *                   properties:
 *                     id:
 *                       type: string
 *                       format: uuid
 *                     name:
 *                       type: string
 *                       example: HVACFanOnOff
 *                     value:
 *                       type: float
 *                       example: 0
 *                   anyOf:
 *                     - required:
 *                       - id
 *                       - value
 *                     - required:
 *                       - name
 *                       - value
 *     responses:
 *       204:
 *         description: The point write arrays were successfully updated
 */
router.put("/sites/:siteId/points/inputs", async (req, res) => {
  const { siteId } = req.params;
  const { points } = req.body;

  // TODO validate points input
  // TODO Validate all point ids/names for existence, ensure that at least one of id/name is present
  // TODO Confirm that points aren't OUTPUT types
  const error = validate(
    { siteId },
    {
      siteId: "required|uuid"
    }
  );
  if (error) return res.status(400).json({ error });

  try {
    for (const point of points) {
      if (point.name && !point.id) {
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

/**
 * @openapi
 * /sites/{siteId}/points/{pointId}:
 *   put:
 *     operationId: Update input point
 *     description: Set the write array value for an input or bidirectional point for a site
 *     tags:
 *       - Site
 *     requestBody:
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               value:
 *                 type: float
 *                 example: 0
 *             required:
 *               - value
 *     responses:
 *       204:
 *         description: The point write array was successfully updated
 */
router.put("/sites/:siteId/points/:pointId", (req, res) => {
  const { siteId, pointId } = req.params;
  const { value } = req.body;

  // TODO validate point for existence
  // TODO Confirm that point isn't an OUTPUT type
  const error = validate(
    { siteId, pointId, value },
    {
      siteId: "required|uuid",
      pointId: "required|uuid",
      value: "required|strict|numeric"
    }
  );
  if (error) return res.status(400).json({ error });

  api
    .writeInputPoint(siteId, pointId, value)
    .then(() => res.sendStatus(204))
    .catch(() => res.sendStatus(500));
});

/**
 * @openapi
 * /sites/{siteId}:
 *   delete:
 *     operationId: Delete site
 *     tags:
 *       - Site
 *     responses:
 *       204:
 *         description: The site was deleted successfully
 *       404:
 *         description: Site ID does not exist
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Error'
 */
router.delete("/sites/:siteId", (req, res) => {
  const { siteId } = req.params;

  const error = validate(
    { siteId },
    {
      siteId: "required|uuid"
    }
  );
  if (error) return res.status(400).json({ error });

  api
    .removeSite(siteId)
    .then((data) => {
      if (data) {
        return res.sendStatus(204);
      } else {
        return res.status(404).json({
          error: `Site ID '${siteId}' does not exist`
        });
      }
    })
    .catch(() => res.sendStatus(500));
});

/**
 * @openapi
 * /sites/{siteId}/start:
 *   post:
 *     operationId: Start run
 *     description: Start a site run
 *     tags:
 *       - Site
 *     requestBody:
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               startDatetime:
 *                 type: string
 *                 description: Start Time
 *                 example: 2022-06-30 12:00:00
 *               endDatetime:
 *                 type: string
 *                 description: End Time
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
 *                 description: Simulate the model in realtime
 *                 example: false
 *             required:
 *               - startDatetime
 *               - endDatetime
 *     responses:
 *       204:
 *         description: The run was started successfully
 *       404:
 *         description: Site ID does not exist
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Error'
 */
router.post("/sites/:siteId/start", async (req, res) => {
  const { siteId } = req.params;
  const { body } = req;

  const timeValidator = /^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/;
  const error = validate(
    { ...body, siteId },
    {
      siteId: "required|uuid",
      startDatetime: ["required", regex(timeValidator)],
      endDatetime: ["required", regex(timeValidator)],
      timescale: "strict|numeric|min:1",
      realtime: "strict|boolean",
      externalClock: "strict|boolean"
    }
  );
  if (error) return res.status(400).json({ error });

  const { timescale, realtime, externalClock } = body;

  if (!(timescale || realtime || externalClock)) {
    return res.status(400).json({
      error: "At least one of timescale, realtime, or externalClock must be specified."
    });
  }

  if (realtime && externalClock) {
    return res.status(400).json({
      error: "Realtime and externalClock cannot both be enabled."
    });
  }

  if (!(await api.findSite(siteId))) {
    return res.status(404).json({
      error: `Site ID '${siteId}' does not exist`
    });
  }

  api
    .startRun(siteId, body)
    .then((data) => {
      if (data?.error) return res.status(400).json(data);
      return res.sendStatus(204);
    })
    .catch(() => res.sendStatus(500));
});

/**
 * @openapi
 * /sites/{siteId}/advance:
 *   post:
 *     operationId: Advance run
 *     description: Advances a site run by one minute
 *     tags:
 *       - Site
 *     responses:
 *       204:
 *         description: The run was advanced successfully
 *       404:
 *         description: Site ID does not exist
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Error'
 */
router.post("/sites/:siteId/advance", (req, res) => {
  const { siteId } = req.params;

  const error = validate(
    { siteId },
    {
      siteId: "required|uuid"
    }
  );
  if (error) return res.status(400).json({ error });

  api
    .advanceRun(siteId)
    .then((data) => {
      if (data) {
        return res.sendStatus(204);
      } else {
        return res.status(404).json({
          error: `Site ID '${siteId}' does not exist`
        });
      }
    })
    .catch(() => res.sendStatus(500));
});

/**
 * @openapi
 * /sites/{siteId}/stop:
 *   post:
 *     operationId: Stop run
 *     description: Stop a site run
 *     tags:
 *       - Site
 *     responses:
 *       204:
 *         description: The run was stopped successfully
 *       404:
 *         description: Site ID does not exist
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Error'
 */
router.post("/sites/:siteId/stop", (req, res) => {
  const { siteId } = req.params;

  const error = validate(
    { siteId },
    {
      siteId: "required|uuid"
    }
  );
  if (error) return res.status(400).json({ error });

  api
    .stopRun(siteId)
    .then((data) => {
      if (data) {
        return res.sendStatus(204);
      } else {
        return res.status(404).json({
          error: `Site ID '${siteId}' does not exist`
        });
      }
    })
    .catch(() => res.sendStatus(500));
});

/**
 * @openapi
 * /aliases:
 *   get:
 *     operationId: List aliases
 *     description: Return list of aliases
 *     tags:
 *       - Alias
 *     responses:
 *       200:
 *         description: Aliases response
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               additionalProperties:
 *                 type: string
 *                 format: uuid
 *             example:
 *               foo: d4e2c041-0389-4933-8aa4-016d80283779
 *               bar: 9e2acb8e-974e-406b-a990-48e9743b01de
 */
router.get("/aliases", (req, res) => {
  api
    .listAliases()
    .then((data) => res.json(data))
    .catch(() => res.sendStatus(500));
});

/**
 * @openapi
 * /aliases/{alias}:
 *   get:
 *     operationId: Get alias
 *     description: Lookup the site id of an alias
 *     tags:
 *       - Alias
 *     responses:
 *       200:
 *         description: Alias response
 *         content:
 *           application/json:
 *             schema:
 *               type: string
 *             example:
 *               4b8c6b40-f818-11ec-a8bd-75570e3e3a28
 *       404:
 *         description: Alias does not exist
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Error'
 */
router.get("/aliases/:alias", (req, res) => {
  const { alias } = req.params;

  api
    .findAlias(alias)
    .then((data) => {
      if (data) {
        return res.json(data);
      } else {
        return res.status(404).json({
          error: `Alias '${alias}' does not exist`
        });
      }
    })
    .catch(() => res.sendStatus(500));
});

/**
 * @openapi
 * /aliases/{alias}:
 *   put:
 *     operationId: Set alias
 *     description: Create or update an alias to point to a site id
 *     tags:
 *       - Alias
 *     responses:
 *       204:
 *         description: The alias was set successfully
 *       404:
 *         description: Site ID does not exist
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Error'
 */
router.put("/aliases/:alias", async (req, res) => {
  const { alias } = req.params;
  const { siteId } = req.body;

  const error = validate(
    { siteId },
    {
      siteId: "required|uuid"
    }
  );
  if (error) return res.status(400).json({ error });

  await api
    .setAlias(alias, siteId)
    .then((data) => {
      if (data) {
        return res.sendStatus(204);
      } else {
        return res.status(404).json({
          error: `Site ID '${siteId}' does not exist`
        });
      }
    })
    .catch(() => res.sendStatus(500));
});

/**
 * @openapi
 * /aliases/{alias}:
 *   delete:
 *     operationId: Delete alias
 *     tags:
 *       - Alias
 *     responses:
 *       204:
 *         description: The alias was deleted successfully
 *       404:
 *         description: Alias does not exist
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Error'
 */
router.delete("/aliases/:alias", (req, res) => {
  const { alias } = req.params;

  api
    .removeAlias(alias)
    .then((deletedCount) => {
      if (deletedCount) return res.sendStatus(204);
      return res.status(404).json({
        error: `Alias '${alias}' does not exist`
      });
    })
    .catch(() => res.sendStatus(500));
});

/**
 * @openapi
 * /version:
 *   get:
 *     operationId: Alfalfa version
 *     description: Return the Alfalfa version and git SHA
 *     tags:
 *       - About
 *     responses:
 *       200:
 *         description: Version response
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Version'
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

/**
 * @openapi
 * /models:
 *   get:
 *     operationId: List models
 *     description: Return list of models
 *     tags:
 *       - Model
 *     responses:
 *       200:
 *         description: Models response
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 data:
 *                   type: array
 *                   items:
 *                     $ref: '#/components/schemas/Model'
 *             example:
 *               data:
 *                 - id: 4b8c6b40-f818-11ec-a8bd-75570e3e3a28
 *                   modelName: refrig_case_osw.zip
 *                   created: 2023-03-09T17:49:13.742Z
 *                   modified: 2023-03-09T17:49:13.742Z
 *                 - id: 82ae8d50-f837-11ec-bda1-355419177ef9
 *                   modelName: refrig_case_osw_2.zip
 *                   created: 2023-03-09T17:49:36.004Z
 *                   modified: 2023-03-09T17:49:36.004Z
 */
router.get("/models", async (req, res) => {
  api
    .listModels()
    .then((data) => res.json({ data }))
    .catch(() => res.sendStatus(500));
});

/**
 * @openapi
 * /models/upload:
 *   post:
 *     operationId: Model upload url
 *     description: Create a POST url to upload a model
 *     tags:
 *       - Model
 *     requestBody:
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               modelName:
 *                 type: string
 *                 description: Upload filename
 *                 example: my_model.zip
 *             required:
 *               - modelName
 *     responses:
 *       200:
 *         description: Upload response
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 url:
 *                   type: string
 *                 fields:
 *                   type: object
 *                   properties:
 *                     bucket:
 *                       type: string
 *                     X-Amz-Algorithm:
 *                       type: string
 *                     X-Amz-Credential:
 *                       type: string
 *                     X-Amz-Date:
 *                       type: string
 *                     key:
 *                       type: string
 *                     Policy:
 *                       type: string
 *                     X-Amz-Signature:
 *                       type: string
 *                 modelID:
 *                   type: string
 *                   format: uuid
 *             example:
 *               url: http://alfalfa.lan:9000/alfalfa
 *               fields:
 *                 bucket: alfalfa
 *                 X-Amz-Algorithm: AWS4-HMAC-SHA256
 *                 X-Amz-Credential: AKIA4MRT6LFGGPHNCKOO/20230309/us-west-1/s3/aws4_request
 *                 X-Amz-Date: 20230309T200246Z
 *                 key: uploads/5c1a0300-beb5-11ed-8531-d9fb035ab2f0/my_model.zip
 *                 Policy: eyJleHBpcmF0aW9uIjoiMjAyMy0wMy0wOVQyMTowMjo0NloiLCJjb25kaXRpb25zIjpbeyJidWNrZXQiOiJhbGZhbGZhIn0seyJYLUFtei1BbGdvcml0aG0iOiJBV1M0LUhNQUMtU0hBMjU2In0seyJYLUFtei1DcmVkZW50aWFsIjoiQUtJQTRNUlQ2TEZHR1BITkNLT08vMjAyMzAzMDkvdXMtd2VzdC0xL3MzL2F3czRfcmVxdWVzdCJ9LHsiWC1BbXotRGF0ZSI6IjIwMjMwMzA5VDIwMDI0NloifSx7ImtleSI6InVwbG9hZHMvNWMxYTAzMDAtYmViNS0xMWVkLTg1MzEtZDlmYjAzNWFiMmYwL215X21vZGVsLnppcCJ9XX0=
 *                 X-Amz-Signature: 7d09a673e65112ee06c7666c34eb9c4ca13cc43f285efc9c1c497befd3a64343
 *               modelID: 5c1a0300-beb5-11ed-8531-d9fb035ab2f0
 */
router.post("/models/upload", async (req, res) => {
  const { modelName } = req.body;

  const error = validate(
    { modelName },
    {
      modelName: ["required", regex(/^.+\.(fmu|zip)$/i)]
    }
  );
  if (error) return res.status(400).json({ error });

  api
    .createUploadPost(modelName)
    .then((data) => res.json(data))
    .catch(() => res.sendStatus(500));
});

/**
 * @openapi
 * /models/{modelId}/createRun:
 *   post:
 *     operationId: Create run
 *     description: Create a run for a model
 *     tags:
 *       - Model
 *     responses:
 *       200:
 *         description: Create run response
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 runID:
 *                   type: string
 *             example:
 *               runID: 28f76e90-bef6-11ed-822a-e3558db4daaf
 *       404:
 *         description: Model ID does not exist
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Error'
 */
router.post("/models/:modelId/createRun", (req, res) => {
  const { modelId } = req.params;

  const error = validate(
    { modelId },
    {
      modelId: "required|uuid"
    }
  );
  if (error) return res.status(400).json({ error });

  api
    .createRunFromModel(modelId)
    .then((data) => {
      if (data) {
        return res.json(data);
      } else {
        return res.status(404).json({
          error: `Model ID '${modelId}' does not exist`
        });
      }
    })
    .catch(() => res.sendStatus(500));
});

/**
 * @openapi
 * /simulations:
 *   get:
 *     operationId: List simulations
 *     description: Return list of simulations
 *     tags:
 *       - Simulation
 *     responses:
 *       200:
 *         description: Simulations response
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 data:
 *                   type: array
 *                   items:
 *                     $ref: '#/components/schemas/Simulation'
 *             example:
 *               data:
 *                 - id: cecbd6e0-c387-11ed-a3bc-35e2ce8e7182
 *                   name: Building 1
 *                   timeCompleted: 2022-03-15T12:00:00.000Z
 *                   status: complete
 *                   url: http://alfalfa.lan:9000/alfalfa/run/cecbd6e0-c387-11ed-a3bc-35e2ce8e7182.tar.gz?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=user%2F20230316%2Fus-west-1%2Fs3%2Faws4_request&X-Amz-Date=20220315T120000Z&X-Amz-Expires=86400&X-Amz-Signature=b46f963fcce33a29bbd2a8f93ea2b5368570acd20033bc5ce1372eeb59e08bfa&X-Amz-SignedHeaders=host&response-content-disposition=attachment%3B%20filename%3D%22Building%201.tar.gz%22&x-id=GetObject
 *                   results: {}
 *                 - id: 9bac1450-c396-11ed-92b6-db6f8d94933d
 *                   name: Building 2
 *                   timeCompleted: 2022-03-16T12:00:00.000Z
 *                   status: complete
 *                   url: http://alfalfa.lan:9000/alfalfa/run/9bac1450-c396-11ed-92b6-db6f8d94933d.tar.gz?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=user%2F20230316%2Fus-west-1%2Fs3%2Faws4_request&X-Amz-Date=20220316T120000Z&X-Amz-Expires=86400&X-Amz-Signature=b46f963fcce33a29bbd2a8f93ea2b5368570acd20033bc5ce1372eeb59e08bfa&X-Amz-SignedHeaders=host&response-content-disposition=attachment%3B%20filename%3D%22Building%202.tar.gz%22&x-id=GetObject
 *                   results: {}
 */
router.get("/simulations", async (req, res) => {
  api
    .listSimulations()
    .then((data) => res.json({ data }))
    .catch(() => res.sendStatus(500));
});

router.get("*", (req, res) => res.sendStatus(404));

export default apiv2;
