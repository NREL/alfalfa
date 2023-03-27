import fsp from "node:fs/promises";
import path from "node:path";
import url from "node:url";
import bodyParser from "body-parser";
import compression from "compression";
import history from "connect-history-api-fallback";
import express from "express";
import { MongoClient } from "mongodb";
import morgan from "morgan";
import { createClient } from "redis";
import alfalfaServer from "./alfalfa-server";
import apiv2 from "./api-v2";

const isProd = process.env.NODE_ENV === "production";

(async () => {
  const redis = createClient({ url: `redis://${process.env.REDIS_HOST}` });
  redis.on("error", (err) => console.error("Redis Client Error", err));
  await redis.connect();

  const mongoClient = await MongoClient.connect(process.env.MONGO_URL, { useUnifiedTopology: true });
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

  let cachedDocs;
  app.get("/redoc", async (req, res) => {
    if (isProd && cachedDocs) {
      return res.type("html").send(cachedDocs);
    }

    const docsPath = path.join(__dirname, "app/redoc-static.html");

    try {
      await fsp.access(docsPath, fsp.constants.F_OK);
      res.sendFile(docsPath);
      if (isProd) cachedDocs = await fsp.readFile(docsPath, "utf-8");
    } catch (e) {
      res.status(404).type("txt").send("Documentation has not been generated");
    }
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

  app.use(history());
  app.use("/", express.static(path.join(__dirname, "app")));

  const server = app.listen(80, () => {
    let { address: host, port } = server.address();
    if (host.length === 0 || host === "::") host = "localhost";

    console.log(`Alfalfa listening at http://${host}:${port}`);
  });
})();
