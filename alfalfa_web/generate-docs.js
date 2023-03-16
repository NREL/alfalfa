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
        description: `${serverType} API v2 Server`
      }
    ],
    tags: [
      {
        name: "About",
        description: "Operations related to the status of Alfalfa"
      },
      {
        name: "Alias",
        description: "Manage site id aliases"
      },
      {
        name: "Model",
        description: "Manage models"
      },
      {
        name: "Simulation",
        description: "Manage completed simulations, including any that may have stopped with errors"
      },
      {
        name: "Site",
        description: "Manage sites"
      },
      {
        name: "Haystack",
        description:
          "Operations using Project Haystack API endpoints\n\n[Haystack API Documentation](https://project-haystack.org/doc/docHaystack/Ops)"
      }
    ],
    "x-tagGroups": [
      {
        name: "Alfalfa API",
        tags: ["About", "Alias", "Model", "Simulation", "Site"]
      },
      {
        name: "Project Haystack API",
        tags: ["Haystack"]
      }
    ],
    components: {
      schemas: {
        Error: {
          type: "object",
          properties: {
            error: {
              type: "string",
              description: "Error message",
              example: "Something went wrong"
            }
          }
        },
        Model: {
          type: "object",
          properties: {
            id: {
              type: "string",
              format: "uuid"
            },
            modelName: {
              type: "string"
            },
            created: {
              type: "dateTime"
            },
            modified: {
              type: "dateTime"
            }
          }
        },
        Point: {
          type: "object",
          properties: {
            id: {
              type: "string",
              format: "uuid"
            },
            name: {
              type: "string"
            },
            type: {
              type: "string",
              enum: ["INPUT", "OUTPUT", "BIDIRECTIONAL"]
            },
            value: {
              type: "float",
              description:
                "Value is only returned for `OUTPUT` and `BIDIRECTIONAL` points if available. Values are not returned when using the `/points/inputs` endpoint"
            }
          },
          required: ["id", "name", "type"]
        },
        Simulation: {
          type: "object",
          properties: {
            id: {
              type: "string",
              format: "uuid"
            },
            name: {
              type: "string"
            },
            timeCompleted: {
              type: "dateTime"
            },
            status: {
              type: "string",
              enum: ["complete", "error"]
            },
            url: {
              type: "string"
            },
            results: {
              type: "object"
            }
          }
        },
        Site: {
          type: "object",
          properties: {
            id: {
              type: "string",
              format: "uuid"
            },
            name: {
              type: "string"
            },
            status: {
              type: "string",
              enum: [
                "created",
                "preprocessing",
                "ready",
                "starting",
                "started",
                "running",
                "stopping",
                "complete",
                "error"
              ]
            },
            simType: {
              type: "string"
            },
            datetime: {
              type: "string"
            },
            uploadTimestamp: {
              type: "dateTime"
            },
            uploadPath: {
              type: "string"
            },
            errorLog: {
              type: "string"
            }
          }
        },
        Version: {
          type: "object",
          properties: {
            version: {
              type: "string",
              description: "The current Alfalfa release version"
            },
            sha: {
              type: "string",
              description: "The git SHA of Alfalfa that is deployed"
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
