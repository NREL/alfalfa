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

const errorHandler = (err, req, res, next) => {
  if (res.headersSent) {
    return next(err);
  }

  console.error(err);

  res.status(500);
  res.json({ error: JSON.parse(JSON.stringify(err, Object.getOwnPropertyNames(err))) });
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
 * /runs:
 *   get:
 *     operationId: List runs
 *     description: Return list of runs
 *     tags:
 *       - Run
 *     responses:
 *       200:
 *         description: Runs response
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
router.get("/runs", async (req, res, next) => {
  api
    .listRuns()
    .then((payload) => res.json({ payload }))
    .catch((err) => {
      next(err);
    });
});

router.param("runId", (req, res, next, id) => {
  const error = validate(
    { id },
    {
      id: "required|uuid"
    }
  );
  if (error) {
    api
      .getAliasByName(id)
      .then((alias) => {
        if (alias != null) {
          api
            .getRun(alias.run)
            .then((run) => {
              if (run != null) {
                req.run = run;
                next();
              } else {
                res.status(500).json({ error: `Alias for '${id}' exists but points to a non-existent Run` });
              }
            })
            .catch(next);
        } else {
          return res.status(400).json({ error });
        }
      })
      .catch(next);
  } else {
    api
      .getRunById(id)
      .then((run) => {
        if (run) {
          req.run = run;
          next();
        } else if (run == null) {
          res.status(404).json({ error: `Run with id '${id}' does not exist` });
        } else {
          res.sendStatus(500);
        }
      })
      .catch(next);
  }
});

router.param("pointId", (req, res, next, id) => {
  const error = validate(
    { id },
    {
      id: "required|uuid"
    }
  );
  if (error) return res.status(400).json({ error });
  api
    .getPointById(req.run, id)
    .then((point) => {
      if (point) {
        req.point = point;
        next();
      } else if (point == null) {
        res.status(404).json({ error: `Point with id '${id}' does not exist` });
      } else {
        res.sendStatus(500);
      }
    })
    .catch(next);
});

router.param("modelId", (req, res, next, id) => {
  const error = validate(
    { id },
    {
      id: "required|uuid"
    }
  );
  if (error) return res.status(400).json({ error });
  api
    .getModelById(id)
    .then((model) => {
      if (model) {
        req.model = model;
        next();
      } else if (model == null) {
        res.status(404).json({ error: `Model with id '${id}' does not exist` });
      } else {
        res.sendStatus(500);
      }
    })
    .catch(next);
});

/**
 * @openapi
 * /runs/{runId}:
 *   get:
 *     operationId: Get run
 *     description: Lookup a run by id
 *     tags:
 *       - Run
 *     parameters:
 *       - $ref: '#/components/parameters/SiteID'
 *     responses:
 *       200:
 *         description: Run response
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
 *         description: Run ID does not exist
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Error'
 */
router.get("/runs/:runId", async (req, res, next) => {
  api
    .formatRun(req.run)
    .then((payload) => {
      res.status(200).json({ payload });
    })
    .catch(next);
});

/**
 * @openapi
 * /runs/{runId}/time:
 *   get:
 *     operationId: Get simulation time
 *     description: Return the current time of the simulation if it has been started
 *     tags:
 *       - Run
 *     parameters:
 *       - $ref: '#/components/parameters/runId'
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
router.get("/runs/:runId/time", async (req, res, next) => {
  api
    .getRunTime(req.run)
    .then((time) => res.json({ payload: { time } }))
    .catch(next);
});

/**
 * @openapi
 * /runs/{runId}/points:
 *   get:
 *     summary: Get the metadata for all points of an associated run
 *     tags:
 *       - Run
 *     parameters:
 *       - $ref: '#/components/parameters/runId'
 *     responses:
 *       '200':
 *         description: OK
 *         content:
 *           application/json:
 *             schema:
 *               type: array
 *               items:
 *                 $ref: '#/components/schemas/pointMetadata'
 */
router.get("/runs/:runId/points", (req, res, next) => {
  api
    .getPointsByRun(req.run)
    .then((points) => {
      return points.map(api.formatPoint);
    })
    .then((payload) => {
      return res.json({ payload });
    })
    .catch(next);
});

/**
 * @openapi
 * /runs/{runId}/points:
 *   post:
 *     summary: Get metadata for specific points
 *     tags:
 *       - Run
 *     parameters:
 *       - $ref: '#/components/parameters/runId'
 *     requestBody:
 *       content:
 *         application/json:
 *           schema:
 *             oneOf:
 *             - type: object
 *               properties:
 *                 points:
 *                   type: array
 *                   items:
 *                     $ref: '#/components/schemas/pointId'
 *             - type: object
 *               properties:
 *                 pointTypes:
 *                   type: array
 *                   items:
 *                     $ref: '#/components/schemas/pointType'
 *           examples:
 *             Points:
 *               value:
 *                 points:
 *                 - 7cf4afb6-9c15-431f-9f50-11bca0870f77
 *                 - Outdoor Air Temperature Sensor
 *             Point Types:
 *               value:
 *                 pointTypes:
 *                 - 'output'
 *     responses:
 *       200:
 *         description: 'OK'
 *         content:
 *           application/json:
 *             schema:
 *               type: array
 *               items:
 *                 $ref: '#/components/schemas/pointMetadata'
 */
router.post("/runs/:runId/points", async (req, res, next) => {
  const { points, pointTypes } = req.body;

  var pointsArr;
  if (points) {
    pointsArr = api.getPointsById(req.run, points);
  } else if (pointTypes) {
    pointsArr = api.getPointsByType(req.run, pointTypes);
  }

  pointsArr
    .then((points) => {
      return points.map(api.formatPoint);
    })
    .then((payload) => {
      res.status(200).json({ payload });
    })
    .catch(next);
});

/**
 * @openapi
 * /runs/{runId}/points/values:
 *   get:
 *     summary: Get values for all points
 *     tags:
 *       - Run
 *     parameters:
 *       - $ref: '#/components/parameters/runId'
 *     responses:
 *       200:
 *         description: 'OK'
 *         content:
 *           application/json:
 *             schema:
 *               type: array
 *               items:
 *                 $ref: '#/components/schemas/pointValue'
 */
router.get("/runs/:runId/points/values", (req, res, next) => {
  api
    .getPointsByRun(req.run)
    .then(async (points) => {
      const payload = {};
      await Promise.all(
        points.map(async (point) => {
          return api.readOutputPoint(req.run, point).then((value) => {
            payload[point.ref_id] = value;
          });
        })
      ).catch(next);

      res.status(200).json({ payload });
    })
    .catch(next);
});

/**
 * @openapi
 * /runs/{runId}/points/values:
 *   post:
 *     summary: Get values for specific points
 *     tags:
 *       - Run
 *     parameters:
 *       - $ref: '#/components/parameters/runId'
 *     requestBody:
 *       content:
 *         application/json:
 *           schema:
 *             oneOf:
 *             - type: object
 *               properties:
 *                 points:
 *                   type: array
 *                   items:
 *                     $ref: '#/components/schemas/pointId'
 *             - type: object
 *               properties:
 *                 pointTypes:
 *                   type: array
 *                   items:
 *                     $ref: '#/components/schemas/pointType'
 *           examples:
 *             Points:
 *               value:
 *                 points:
 *                 - 7cf4afb6-9c15-431f-9f50-11bca0870f77
 *                 - Outdoor Air Temperature Sensor
 *             Point Types:
 *               value:
 *                 pointTypes:
 *                 - 'output'
 *     responses:
 *       200:
 *         description: 'OK'
 *         content:
 *           application/json:
 *             schema:
 *               type: array
 *               items:
 *                 $ref: '#/components/schemas/pointValue'
 */
router.post("/runs/:runId/points/values", async (req, res, next) => {
  const { points, pointTypes } = req.body;

  var pointsArr;
  if (points) {
    pointsArr = await api.getPointsById(req.run, points);
  } else if (pointTypes) {
    pointsArr = await api.getPointsByType(req.run, pointTypes);
  }

  const payload = {};
  await Promise.all(
    pointsArr.map(async (point) => {
      return api.readOutputPoint(req.run, point).then((value) => {
        payload[point.ref_id] = value;
      });
    })
  ).catch(next);

  res.status(200).json({ payload });
});

/**
 * @openapi
 * /runs/{runId}/points/values:
 *   put:
 *     summary: Put new values to specified points
 *     tags:
 *       - points
 *       - runs
 *     parameters:
 *       - $ref: 'components.yml#/components/parameters/runId'
 *     requestBody:
 *       content:
 *         application/json:
 *           schema:
 *             type: array
 *             items:
 *               $ref: 'components.yml#/components/schemas/pointValue'
 *           example:
 *             - id: 7cf4afb6-9c15-431f-9f50-11bca0870f77
 *               value: 7.0
 *             - id: 76d43bc5-9c56-48a8-b9e5-61a651b8dee4
 *               value: 12.6
 *             - id: 58b717ad-20a7-4cc6-89f1-f99b1938b0ef
 *               value: 0.5
 *     responses:
 *       200:
 *         description: 'Points successfully updated'
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 success:
 *                   type: boolean
 *                 errors:
 *                   type: array
 *                   items:
 *                     type: string
 */
router.put("/runs/:runId/points/values", async (req, res, next) => {
  const { points } = req.body;

  const errors = [];

  const pointWrites = [];

  await Promise.all(
    Object.entries(points).map(async ([pointId, value]) => {
      return await api
        .getPointById(req.run, pointId)
        .then((point) => {
          if (point) {
            pointWrites.push([point, value]);
          } else {
            errors.push({ message: `Point with id '${pointId}' does not exist` });
          }
          return api.validatePointWrite(point, value).catch((err) => {
            errors.push(JSON.parse(JSON.stringify(err, Object.getOwnPropertyNames(err))));
          });
        })
        .catch((err) => {
          errors.push(JSON.parse(JSON.stringify(err, Object.getOwnPropertyNames(err))));
        });
    })
  );

  if (errors.length > 0) return res.status(400).json({ error: errors });

  try {
    const promises = pointWrites.map(([point, value]) => {
      return api.writeInputPoint(req.run, point, value);
    });
    await Promise.all(promises);
    res.sendStatus(204);
  } catch (e) {
    next(e);
  }
});

/**
 * @openapi
 * /runs/{runId}/points/{pointId}:
 *   get:
 *     summary: Get data for point of a given ID
 *     tags:
 *       - Run
 *     parameters:
 *       - $ref: '#/components/parameters/runId'
 *       - $ref: '#/components/parameters/pointId'
 *     responses:
 *       '200':
 *         description: OK
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/pointData'
 */
router.get("/runs/:runId/points/:pointId", (req, res, next) => {
  if (req.point.point_type != "INPUT") {
    api
      .readOutputPoint(req.run, req.point)
      .then((value) => {
        const formattedPoint = api.formatPoint(req.point);
        formattedPoint.value = value;
        res.status(200).json({ payload: formattedPoint });
      })
      .catch(next);
  } else {
    res.status(200).json({ payload: api.formatPoint(req.point) });
  }
});

/**
 * @openapi
 * /runs/{runId}/points/{pointId}:
 *   put:
 *     summary: Set value for point of given ID
 *     tags:
 *       - Run
 *     parameters:
 *       - $ref: '#/components/parameters/runId'
 *       - $ref: '#/components/parameters/pointId'
 *     requestBody:
 *       content:
 *         application/json:
 *           schema:
 *             $ref: '#/components/schemas/pointValue'
 *     responses:
 *       204:
 *         description: The point was successfully updated
 */
router.put("/runs/:runId/points/:pointId", (req, res, next) => {
  // TODO Confirm that point isn't an OUTPUT type
  if (value !== null) {
    const error = validate(
      { value },
      {
        value: "required|strict|numeric"
      }
    );
    if (error) return res.status(400).json({ error });
  }

  api
    .writeInputPoint(req.run, req.point, value)
    .then(() => res.sendStatus(204))
    .catch(next);
});

/**
 * @openapi
 * /runs/{runId}:
 *   delete:
 *     operationId: Delete run
 *     tags:
 *       - Run
 *     parameters:
 *       - $ref: '#/components/parameters/runId'
 *     responses:
 *       204:
 *         description: The run was deleted successfully
 *       404:
 *         description: Run ID does not exist
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Error'
 */
router.delete("/runs/:runId", (req, res, next) => {
  api
    .removeRun(req.run)
    .then(() => {
      res.sendStatus(204);
    })
    .catch(next);
});

/**
 * @openapi
 * /runs/{runId}/start:
 *   post:
 *     operationId: Start run
 *     description: Start a run
 *     tags:
 *       - Run
 *     parameters:
 *       - $ref: '#/components/parameters/runId'
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
 *                 description: The run will only advance when explicitly told to via an external call
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
 *         description: Run ID does not exist
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Error'
 */
router.post("/runs/:runId/start", async (req, res, next) => {
  const { body } = req;

  const timeValidator = /^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/;
  const error = validate(
    { ...body },
    {
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

  api
    .startRun(req.run, body)
    .then((data) => {
      if (data?.error) return res.status(400).json(data);
      return res.sendStatus(204);
    })
    .catch(next);
});

/**
 * @openapi
 * /runs/{runId}/advance:
 *   post:
 *     operationId: Advance run
 *     description: Advances a run by one minute
 *     tags:
 *       - Run
 *     parameters:
 *       - $ref: '#/components/parameters/runId'
 *     responses:
 *       204:
 *         description: The run was advanced successfully
 *       404:
 *         description: Run ID does not exist
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Error'
 */
router.post("/runs/:runId/advance", (req, res, next) => {
  api
    .advanceRun(req.run)
    .then(() => {
      res.sendStatus(204);
    })
    .catch(next);
});

/**
 * @openapi
 * /runs/{runId}/stop:
 *   post:
 *     operationId: Stop run
 *     description: Stop a run
 *     tags:
 *       - Run
 *     parameters:
 *       - $ref: '#/components/parameters/runId'
 *     responses:
 *       204:
 *         description: The run was stopped successfully
 *       404:
 *         description: Run ID does not exist
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Error'
 */
router.post("/runs/:runId/stop", (req, res, next) => {
  // If the run is already stopping or stopped there is no need to send message
  if (["STOPPING", "STOPPED", "COMPLETE"].includes(req.run.status)) {
    res.sendStatus(204);
  }
  api
    .stopRun(req.run)
    .then(() => {
      res.sendStatus(204);
    })
    .catch(next);
});

/**
 * @openapi
 * /runs/{runId}/download:
 *   get:
 *     operationId: Download run
 *     description: Download run by redirecting to the S3 tarball url
 *     tags:
 *       - Run
 *     parameters:
 *       - $ref: '#/components/parameters/runId'
 *     responses:
 *       302:
 *         description: Download response
 *         headers:
 *           Location:
 *             schema:
 *               type: string
 *               format: url
 *         content:
 *           application/octet-stream:
 *             schema:
 *               type: string
 *               format: binary
 */
router.get("/runs/:runId/download", (req, res, next) => {
  api
    .getRunDownloadPath(req.run)
    .then((url) => {
      res.redirect(url);
    })
    .catch(next);
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
router.get("/aliases", (req, res, next) => {
  api
    .listAliases()
    .then((payload) => res.json({ payload }))
    .catch(next);
});

/**
 * @openapi
 * /aliases/{alias}:
 *   put:
 *     operationId: Set alias
 *     description: Create or update an alias to point to a run id
 *     tags:
 *       - Alias
 *     parameters:
 *       - $ref: '#/components/parameters/Alias'
 *     responses:
 *       204:
 *         description: The alias was set successfully
 *       404:
 *         description: Run ID does not exist
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Error'
 */
router.put("/aliases/:alias", async (req, res, next) => {
  const { alias } = req.params;
  const { runId } = req.body;

  const error = validate(
    { runId },
    {
      runId: "required|uuid"
    }
  );
  if (error) return res.status(400).json({ error });

  await api
    .getRunById(runId)
    .then((run) => {
      if (run == null) {
        return res.status(400).json({
          error: `Run with ID '${runId}' does not exist`
        });
      }
      api
        .setAlias(alias, run)
        .then(() => {
          return res.sendStatus(204);
        })
        .catch(next);
    })
    .catch(next);
});

router.all("/aliases/:alias", (req, res, next) => {
  const { alias: aliasName } = req.params;
  api
    .getAliasByName(aliasName)
    .then((alias) => {
      if (alias) {
        req.alias = alias;
        api.getRun(alias.run).then((run) => {
          if (run) {
            req.run = run;
            next();
          } else {
            next(Error(`Alias with name '${aliasName}' contains a reference to a Run which does not exist`));
          }
        });
      } else if (alias == null) {
        res.status(404).json({ error: `Alias with name '${aliasName}' does not exist` });
      } else {
        res.sendStatus(500);
      }
    })
    .catch(next);
});

/**
 * @openapi
 * /aliases/{alias}:
 *   get:
 *     operationId: Get alias
 *     description: Lookup the run id of an alias
 *     tags:
 *       - Alias
 *     parameters:
 *       - $ref: '#/components/parameters/Alias'
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
  res.json({ payload: req.run.ref_id });
});

/**
 * @openapi
 * /aliases/{alias}:
 *   delete:
 *     operationId: Delete alias
 *     tags:
 *       - Alias
 *     parameters:
 *       - $ref: '#/components/parameters/Alias'
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
router.delete("/aliases/:alias", (req, res, next) => {
  api
    .removeAlias(req.alias)
    .then(() => {
      return res.sendStatus(204);
    })
    .catch(next);
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
    .then((payload) => res.json({ payload }))
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
router.post("/models/upload", async (req, res, next) => {
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
    .then((payload) => res.json({ payload }))
    .catch(next);
});

router.get("/models/:modelId", (req, res) => {
  res.status(200).json({ payload: api.formatModel(req.model) });
});

/**
 * @openapi
 * /models/{modelId}/createRun:
 *   post:
 *     operationId: Create run
 *     description: Create a run for a model
 *     tags:
 *       - Model
 *     parameters:
 *       - $ref: '#/components/parameters/ModelID'
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
router.post("/models/:modelId/createRun", (req, res, next) => {
  api
    .createRunFromModel(req.model)
    .then((payload) => {
      return res.json({ payload });
    })
    .catch(next);
});

router.get("/models/:modelId/download", (req, res, next) => {
  api
    .getModelDownloadPath(req.model)
    .then((url) => {
      res.redirect(url);
    })
    .catch(next);
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
    .then((payload) => res.json({ payload }))
    .catch(() => res.sendStatus(500));
});

router.get("*", (req, res) => res.sendStatus(404));

router.use(errorHandler);

export default apiv2;
