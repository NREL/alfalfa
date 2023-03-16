import fsp from "node:fs/promises";
import path from "node:path";
import url from "node:url";
import bodyParser from "body-parser";
import compression from "compression";
import historyApiFallback from "connect-history-api-fallback";
import express from "express";
import { MongoClient } from "mongodb";
import morgan from "morgan";
import { createClient } from "redis";
import alfalfaServer from "./alfalfa-server";
import apiv2 from "./api-v2";

const redis = createClient({ host: process.env.REDIS_HOST });

MongoClient.connect(process.env.MONGO_URL, { useUnifiedTopology: true })
  .then((mongoClient) => {
    const db = mongoClient.db(process.env.MONGO_DB_NAME);

    const app = express();
    app.disable("x-powered-by");
    app.use(compression({ threshold: 0 }));
    app.locals.alfalfaServer = new alfalfaServer(db, redis);

    if (process.env.LOGGING === "true") {
      app.use(morgan("combined"));
    }

    app.use(bodyParser.text({ type: "text/*" }));
    // If you are using JSON instead of ZINC you need this
    app.use((req, res, next) => {
      bodyParser.json()(req, res, (err) => {
        if (err) return res.status(400).json({ error: "Invalid JSON" });
        next();
      });
    });

    app.get("/redoc", (req, res) => {
      const docsPath = path.join(__dirname, "/app/docs.html");

      fsp
        .access(docsPath, fsp.constants.F_OK)
        .then(() => res.sendFile(docsPath))
        .catch(() => res.status(404).type("txt").send("Documentation has not been generated"));
    });

    app.use("/api/v2/", apiv2({ api: app.locals.alfalfaServer.api }));

    app.all("/haystack/*", (req, res) => {
      const path = url.parse(req.url).pathname.replace(/^\/haystack/, "");
      if (path === "/") {
        return res.redirect(301, "/docs");
      }

      // parse URI path into "/{opName}/...."
      let slash = path.indexOf("/", 1);
      if (slash < 0) slash = path.length;
      const opName = path.substring(1, slash);

      // resolve the op
      app.locals.alfalfaServer.op(opName, false, (err, op) => {
        if (!op) {
          return res.status(404).type("txt").send(`Invalid op '${opName}'`);
        }

        // route to the op
        op.onServiceOp(app.locals.alfalfaServer, req, res, (err) => {
          if (err) {
            console.log(err.stack);
            throw err;
          }
          res.end();
        });
      });
    });

    // Redirect incomplete and nonexistent API URLs to /docs
    app.get("/api/*", (req, res) => {
      res.redirect(301, "/docs");
    });
    app.get("/haystack", (req, res) => {
      res.redirect(301, "/docs#tag/Haystack");
    });

    app.use(historyApiFallback());
    app.use("/", express.static(path.join(__dirname, "app")));

    const server = app.listen(80, () => {
      let { address: host, port } = server.address();
      if (host.length === 0 || host === "::") host = "localhost";

      console.log(`Alfalfa listening at http://${host}:${port}`);
    });
  })
  .catch((err) => {
    console.log(err);
  });
