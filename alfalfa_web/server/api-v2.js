/***********************************************************************************************************************
 *  Copyright (c) 2008-2022, Alliance for Sustainable Energy, LLC, and other contributors. All rights reserved.
 *
 *  Redistribution and use in source and binary forms, with or without modification, are permitted provided that the
 *  following conditions are met:
 *
 *  (1) Redistributions of source code must retain the above copyright notice, this list of conditions and the following
 *  disclaimer.
 *
 *  (2) Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following
 *  disclaimer in the documentation and/or other materials provided with the distribution.
 *
 *  (3) Neither the name of the copyright holder nor the names of any contributors may be used to endorse or promote products
 *  derived from this software without specific prior written permission from the respective party.
 *
 *  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDER(S) AND ANY CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
 *  INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 *  DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER(S), ANY CONTRIBUTORS, THE UNITED STATES GOVERNMENT, OR THE UNITED
 *  STATES DEPARTMENT OF ENERGY, NOR ANY OF THEIR EMPLOYEES, BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
 *  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
 *  USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
 *  STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
 *  ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 ***********************************************************************************************************************/

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
  const cursor = db.collection("runs").find();
  for await (const doc of cursor) {
    if (doc) docs[doc._id] = doc;
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
  const doc = await db.collection("runs").findOne({ _id: modelId });

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

  const { sim_type } = await db.collection("runs").findOne({ _id: modelId });
  const { startDatetime, endDatetime, timescale, realtime, externalClock } = body;
  const params = {
    MessageBody: `{
      "job": "alfalfa_worker.jobs.${sim_type === "MODELICA" ? "modelica" : "openstudio"}.StepRun",
      "params": {
        "run_id": "${modelId}",
        "start_datetime": "${startDatetime}",
        "end_datetime": "${endDatetime}",
        "timescale": ${timescale || 5},
        "realtime": ${!!realtime},
        "external_clock": ${!!externalClock}
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
