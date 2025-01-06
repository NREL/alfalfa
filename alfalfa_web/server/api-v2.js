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
  res.json({ message: err.message, payload: err.stack });
};

router.get("/", (req, res) => {
  res.redirect(301, "/docs");
});

// Remove trailing slashes
router.get(/\/$/, (req, res) => {
  res.redirect(301, `${route}${req.url.slice(0, -1)}`);
});

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
                res.status(500).json({ message: `Alias for '${id}' exists but points to a non-existent Run` });
              }
            })
            .catch(next);
        } else {
          return res.status(400).json({ message: error });
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
          res.status(404).json({ message: `Run with id '${id}' does not exist` });
        } else {
          res.status(500).json({ message: "Unknown error occurred" });
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
  if (error) return res.status(400).json({ message: error });
  api
    .getPointById(req.run, id)
    .then((point) => {
      if (point) {
        req.point = point;
        next();
      } else if (point == null) {
        res.status(404).json({ message: `Point with id '${id}' does not exist` });
      } else {
        res.status(500).json({ message: "Unknown error occurred" });
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
  if (error) return res.status(400).json({ message: error });
  api
    .getModelById(id)
    .then((model) => {
      if (model) {
        req.model = model;
        next();
      } else if (model == null) {
        res.status(404).json({ message: `Model with id '${id}' does not exist` });
      } else {
        res.status(500).json({ message: "Unknown error occurred" });
      }
    })
    .catch(next);
});

router.get("/runs/:runId", async (req, res, next) => {
  api
    .formatRun(req.run)
    .then((payload) => {
      res.status(200).json({ payload });
    })
    .catch(next);
});

router.get("/runs/:runId/time", async (req, res, next) => {
  api
    .getRunTime(req.run)
    .then((time) => res.json({ payload: { time } }))
    .catch(next);
});

router.get("/runs/:runId/log", async (req, res, next) => {
  api
    .getRunLog(req.run)
    .then((log) => res.json({ payload: { log } }))
    .catch(next);
});

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

router.get("/runs/:runId/points/values", (req, res, next) => {
  api
    .getPointsByType(req.run, ["OUTPUT", "BIDIRECTIONAL"])
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
            errors.push(`Point with id '${pointId}' does not exist`);
          }
          return api.validatePointWrite(point, value).catch((err) => {
            errors.push(JSON.parse(JSON.stringify(err, Object.getOwnPropertyNames(err))));
          });
        })
        .catch((err) => {
          errors.push(err.message);
        });
    })
  );

  if (errors.length > 0) return res.status(400).json({ message: "Some points writes are not valid", payload: errors });

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

router.put("/runs/:runId/points/:pointId", (req, res, next) => {
  const { value } = req.body;

  if (req.point.point_type == "OUTPUT") {
    return res
      .status(400)
      .json({ message: `Point '${req.point.ref_id}' is of type '${req.point.point_type}' and cannot be written to` });
  }

  if (value !== null) {
    const error = validate(
      { value },
      {
        value: "required|strict|numeric"
      }
    );
    if (error) return res.status(400).json({ message: error });
  }

  api
    .writeInputPoint(req.run, req.point, value)
    .then(() => res.sendStatus(204))
    .catch(next);
});

router.delete("/runs/:runId", (req, res, next) => {
  api
    .removeRun(req.run)
    .then(() => {
      res.sendStatus(204);
    })
    .catch(next);
});

router.post("/runs/:runId/start", (req, res, next) => {
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
  if (error) return res.status(400).json({ message: error });

  const { timescale, realtime, externalClock } = body;

  if (!(timescale || realtime || externalClock)) {
    return res.status(400).json({
      message: "At least one of timescale, realtime, or externalClock must be specified."
    });
  }

  if (realtime && externalClock) {
    return res.status(400).json({
      message: "Realtime and externalClock cannot both be enabled."
    });
  }

  api
    .startRun(req.run, body)
    .then((data) => {
      if (data?.error) return res.status(400).json({ message: "Error occurred starting run", payload: data });
      return res.sendStatus(204);
    })
    .catch(next);
});

router.post("/runs/:runId/advance", (req, res, next) => {
  api
    .advanceRun(req.run)
    .then(() => {
      res.sendStatus(204);
    })
    .catch(next);
});

router.post("/runs/:runId/stop", (req, res, next) => {
  // If the run is already stopping or stopped there is no need to send message
  if (["STOPPING", "COMPLETE", "ERROR", "READY"].includes(req.run.status)) {
    res.sendStatus(204);
  }
  api
    .stopRun(req.run)
    .then(() => {
      res.sendStatus(204);
    })
    .catch(next);
});

router.get("/runs/:runId/download", (req, res, next) => {
  api
    .getRunDownloadPath(req.run)
    .then((url) => {
      res.redirect(url);
    })
    .catch(next);
});

router.get("/aliases", (req, res, next) => {
  api
    .listAliases()
    .then((payload) => res.json({ payload }))
    .catch(next);
});

router.put("/aliases/:alias", async (req, res, next) => {
  const { alias } = req.params;
  const { runId } = req.body;

  const error = validate(
    { runId },
    {
      runId: "required|uuid"
    }
  );
  if (error) return res.status(400).json({ message: error });

  await api
    .getRunById(runId)
    .then((run) => {
      if (run == null) {
        return res.status(400).json({
          message: `Run with ID '${runId}' does not exist`
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
        res.status(404).json({ message: `Alias with name '${aliasName}' does not exist` });
      } else {
        res.status(500).json({ message: "Unknown error occurred" });
      }
    })
    .catch(next);
});

router.get("/aliases/:alias", (req, res) => {
  res.json({ payload: req.run.ref_id });
});

router.delete("/aliases/:alias", (req, res, next) => {
  api
    .removeAlias(req.alias)
    .then(() => {
      return res.sendStatus(204);
    })
    .catch(next);
});

router.get("/version", (req, res) => {
  let sha = {};
  const shaPath = path.resolve(__dirname, "./sha.json");
  if (existsSync(shaPath)) {
    sha = JSON.parse(readFileSync(shaPath, "utf-8"));
  }
  res.json({ payload: { version, ...sha } });
});

router.get("/models", async (req, res, next) => {
  api
    .listModels()
    .then((payload) => res.json({ payload }))
    .catch(next);
});

router.post("/models/upload", async (req, res, next) => {
  const { modelName } = req.body;

  const error = validate(
    { modelName },
    {
      modelName: ["required", regex(/^.+\.(fmu|zip)$/i)]
    }
  );
  if (error) return res.status(400).json({ message: error });

  api
    .createUploadPost(modelName)
    .then((payload) => res.json({ payload }))
    .catch(next);
});

router.get("/models/:modelId", (req, res) => {
  res.status(200).json({ payload: api.formatModel(req.model) });
});

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

router.all("*", (req, res) => res.status(404).json({ message: "Page not found" }));

router.use(errorHandler);

export default apiv2;
