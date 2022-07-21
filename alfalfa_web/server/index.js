import AWS from "aws-sdk";
import bodyParser from "body-parser";
import compression from "compression";
import historyApiFallback from "connect-history-api-fallback";
import cors from "cors";
import express from "express";
import { graphqlHTTP } from "express-graphql";
import { MongoClient } from "mongodb";
import morgan from "morgan";
import path from "path";
import { createClient } from "redis";
import url from "url";
import { Advancer } from "./advancer";
import alfalfaServer from "./alfalfa-server";
import apiv2 from "./api-v2";
import { schema } from "./schema";

const isProd = process.env.NODE_ENV === "production";

const client = new AWS.S3({ endpoint: process.env.S3_URL });

const redis = createClient({ host: process.env.REDIS_HOST });

const pub = redis.duplicate();
const sub = redis.duplicate();
const advancer = new Advancer(redis, pub, sub);

MongoClient.connect(process.env.MONGO_URL, { useUnifiedTopology: true })
  .then((mongoClient) => {
    const app = express();
    app.use(compression());
    app.disable("x-powered-by");

    if (!isProd) {
      // Apollo Studio
      app.use(cors());
    }

    if (process.env.LOGGING === "true") {
      app.use(morgan("combined"));
    }

    const db = mongoClient.db(process.env.MONGO_DB_NAME);

    app.locals.alfalfaServer = new alfalfaServer(db, redis, pub, sub);

    app.use("/graphql", (request, response) => {
      return graphqlHTTP({
        graphiql: !isProd,
        pretty: !isProd,
        schema,
        context: {
          request,
          db,
          advancer
        }
      })(request, response);
    });

    app.use(bodyParser.text({ type: "text/*" }));
    app.use(bodyParser.json()); // if you are using JSON instead of ZINC you need this

    app.get("/docs", (req, res) => {
      res.sendFile(path.join(__dirname, "/app/docs.html"));
    });

    // Create a post url for file uploads
    // from a browser
    app.post("/upload-url", (req, res) => {
      // Construct a new postPolicy.
      const params = {
        Bucket: process.env.S3_BUCKET,
        Fields: {
          key: req.body.name
        }
      };

      client.createPresignedPost(params, function (err, data) {
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
          res.send(JSON.stringify(data));
          res.end();
        }
      });
    });

    app.use("/api/v2/", apiv2({ db }));

    app.all("/haystack/*", function (req, res) {
      const path = url.parse(req.url).pathname.replace(/^\/haystack/, "");

      // parse URI path into "/{opName}/...."
      let slash = path.indexOf("/", 1);
      if (slash < 0) slash = path.length;
      const opName = path.substring(1, slash);

      // resolve the op
      app.locals.alfalfaServer.op(opName, false, function (err, op) {
        if (typeof op === "undefined" || op === null) {
          res.status(404);
          res.send("404 Not Found");
          res.end();
          return;
        }

        // route to the op
        op.onServiceOp(app.locals.alfalfaServer, req, res, function (err) {
          if (err) {
            console.log(err.stack);
            throw err;
          }
          res.end();
        });
      });
    });

    app.use(historyApiFallback());
    app.use("/", express.static(path.join(__dirname, "./app")));

    let server = app.listen(80, () => {
      let { address: host, port } = server.address();

      if (host.length === 0 || host === "::") host = "localhost";

      console.log(`Node Haystack Toolkit listening at http://${host}:${port}`);
    });
  })
  .catch((err) => {
    console.log(err);
  });
