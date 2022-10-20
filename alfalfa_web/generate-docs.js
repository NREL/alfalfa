const fs = require("fs");
if (fs.existsSync("../.env")) require("dotenv").config({ path: "../.env" });
const mkdirp = require("mkdirp");
const npmRun = require("npm-run");
const swaggerJsdoc = require("swagger-jsdoc");
const { version } = require("./package.json");

const serverType = process.env.NODE_ENV === "production" ? "Production" : "Development";

const openapiSpecification = swaggerJsdoc({
  apis: ["./server/api-v2.js", "./server/api-haystack.js"],
  definition: {
    openapi: "3.1.0",
    info: {
      title: "Alfalfa API Documentation",
      version,
      description:
        "Alfalfa transforms Building Energy Models (BEMs) into virtual buildings by providing industry standard building control interfaces for interacting with models as they run",
      "x-logo": {
        url: "/assets/alfalfa.svg"
      }
    },
    servers: [
      {
        url: "/api/v2",
        description: `${serverType} server`
      }
    ],
    tags: [
      {
        name: "Alfalfa",
        description: "Alfalfa API v2 endpoints"
      },
      {
        name: "Haystack",
        description: "Project Haystack API endpoints"
      }
    ],
    components: {
      schemas: {
        Model: {
          type: "object",
          properties: {
            id: {
              type: "string"
            },
            description: {
              type: "string"
            },
            uploadTimestamp: {
              type: "string"
            },
            uploadPath: {
              type: "string"
            }
          }
        }
      }
    }
  }
});

mkdirp.sync("build/app/assets");
fs.writeFileSync("build/app/openapi.json", JSON.stringify(openapiSpecification));

npmRun.execSync("redoc-cli build openapi.json -t ../../docs.hbs", { cwd: __dirname + "/build/app" });

fs.copyFileSync("alfalfa.svg", "build/app/assets/alfalfa.svg");
fs.renameSync("build/app/redoc-static.html", "build/app/docs.html");
