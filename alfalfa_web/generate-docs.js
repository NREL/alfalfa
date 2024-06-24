const fs = require("fs");
if (fs.existsSync("../.env")) require("dotenv").config({ path: "../.env" });
const mkdirp = require("mkdirp");
const npmRun = require("npm-run");
const swaggerJsdoc = require("swagger-jsdoc");
const { version } = require("./package.json");

const serverType = process.env.NODE_ENV === "production" ? "Production" : "Development";

const openapiSpecification = swaggerJsdoc({
  apis: ["./server/api-v2.js", "./server/api-haystack.js", "./api.yml"],
  definition: {
    openapi: "3.1.0",
    info: {
      title: "Alfalfa API Documentation",
      version,
      description:
        "Alfalfa transforms Building Energy Models (BEMs) into virtual buildings by providing industry standard building control interfaces for interacting with models as they run",
      "x-logo": {
        url: "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNTYgOTIuMzYzIj48cGF0aCBmaWxsPSIjODM5NGEwIiBkPSJNMzUuNDE4IDg3LjM2MWMuMDAyLTEyLjcyMS4wMTMtMzEuNTE5LS4wMDItNDQuMjQxIDUuMzUzIDMuNTM4IDEwLjY1OSA3LjE0NiAxNi4wMTEgMTAuNjgzLjAxMSAzLjE1LS4wMDMgMzAuNDEuMDAzIDMzLjU1OEgzNS40MThabS0xLjQwNyAwYzAtMy41My0uMDA2LTguOTQ0LS4wMDItMTIuNDc1LS4wMDctLjM5LjAzOC0uNzg5LS4wNDMtMS4xNzNsLS4xMzUtLjEyOGMtMi42MDgtMS45NjUtNS4yMzItMy45MTMtNy44NDktNS44NjktMi4yMjMgMS42MjgtNC40MDcgMy4zMDctNi42MjIgNC45NDYtLjQ1Ni4zMzUtLjkyMi42Ni0xLjM1OSAxLjAyMWwuMDA0IDEzLjY3OGgxNi4wMDZaIi8+PHBhdGggZmlsbD0iIzAwNTE5MSIgZD0iTTEwOS4xNDQgODcuMzYyaC03LjE5NWwtMi4wMDMtNS42ODNIODkuODg5bC0yLjAwMyA1LjY4M2gtNi44NjhsMTAuNjI5LTI4LjI0OWg2Ljg2OGwxMC42MjkgMjguMjQ5Wk05OC40MzMgNzYuNTI4bC0zLjUxNi0xMC4xMzktMy41MTYgMTAuMTM5aDcuMDMyWm0yOC43MzkgMTAuODM0aC0xNi4zNTNWNTkuMTU0aDYuNTgydjIyLjczaDkuNzcxdjUuNDc4Wm0xOS44NjgtMjIuOTM0aC0xMS4wMzh2Ni45MDloMTAuMzg0djUuMjc0aC0xMC4zODR2MTAuNzUyaC02LjU4MlY1OS4xNTVoMTcuNjJ2NS4yNzRabTI2LjUzMiAyMi45MzNoLTcuMTk1bC0yLjAwMy01LjY4M2gtMTAuMDU3bC0yLjAwMyA1LjY4M2gtNi44NjhsMTAuNjI5LTI4LjI0OWg2Ljg2OGwxMC42MjkgMjguMjQ5Wm0tMTAuNzExLTEwLjgzNC0zLjUxNi0xMC4xMzktMy41MTYgMTAuMTM5aDcuMDMyWk0xOTEuNiA4Ny4zNjFoLTE2LjM1M1Y1OS4xNTNoNi41ODJ2MjIuNzNoOS43NzF2NS40NzhabTE5Ljg2OC0yMi45MzRIMjAwLjQzdjYuOTA5aDEwLjM4NHY1LjI3NEgyMDAuNDN2MTAuNzUyaC02LjU4MlY1OS4xNTRoMTcuNjJ2NS4yNzRaTTIzOCA4Ny4zNmgtNy4xOTVsLTIuMDAzLTUuNjgzaC0xMC4wNTdsLTIuMDAzIDUuNjgzaC02Ljg2OGwxMC42MjktMjguMjQ5aDYuODY4TDIzOCA4Ny4zNlptLTEwLjcxMS0xMC44MzQtMy41MTYtMTAuMTM5LTMuNTE2IDEwLjEzOWg3LjAzMloiLz48cGF0aCBmaWxsPSIjNDFhN2RiIiBkPSJNNzIuMzY2IDQxLjM5N3YzLjg3MmgtLjAwNmMtMy44MiAwLTYuOTQxIDMuMTEtNi45NDEgNi45NDFzMy4xMjEgNi45NDEgNi45NDEgNi45NDFoLjAwNXYzLjg3M2MtLjgyNi0uMDAyLTEuNjg3LS4xMzQtMy4xOC0uNDA3bC0xLjgyOSAzLjE2NGExNC4zNjcgMTQuMzY3IDAgMCAxLTQuMjUxLTIuNDU0bDEuODI5LTMuMTY0Yy0xLjk2OS0yLjMwMy0yLjE2My0yLjYzNy0zLjE3NS01LjQ5OUg1OC4xYTE1LjAyIDE1LjAyIDAgMCAxIDAtNC45MDdoMy42NTljMS4wMjItMi44ODQgMS4yNDgtMy4yNSAzLjE3NS01LjQ5OWwtMS44MjktMy4xNjRhMTQuMzY3IDE0LjM2NyAwIDAgMSA0LjI1MS0yLjQ1NGwxLjgyOSAzLjE2NGMxLjQ4Mi0uMjcxIDIuMzExLS40MTEgMy4xODEtLjQwN1pNNjguODYyIDUyLjIxYTMuNTA0IDMuNTA0IDAgMCAwIDMuNDk3IDMuNDk3aC4wMDV2LTYuOTk1aC0uMDA2YTMuNTA0IDMuNTA0IDAgMCAwLTMuNDk3IDMuNDk3Wm0xLjEwOCAxNS45NmEyLjUxNSAyLjUxNSAwIDAgMS0yLjkyNyAxLjE0MSAxOC4xNjUgMTguMTY1IDAgMCAxLTYuODIzLTMuOTQ5IDIuNDc0IDIuNDc0IDAgMCAxLS40NzMtMy4wODhsMS4wMjItMS43NzZhMTMuODY5IDEzLjg2OSAwIDAgMS0xLjM3Ny0yLjM4OWgtMi4wNDVhMi40OTggMi40OTggMCAwIDEtMi40NDMtMS45NTkgMTguMDE3IDE4LjAxNyAwIDAgMSAwLTcuODc3IDIuNDkgMi40OSAwIDAgMSAyLjQ0My0xLjk1OWgyLjA0NWMuMzc3LS44MzkuODM5LTEuNjM2IDEuMzc3LTIuMzg5bC0xLjAyMi0xLjc3NmEyLjQ3NyAyLjQ3NyAwIDAgMSAuNDczLTMuMDg4IDE3LjgxNSAxNy44MTUgMCAwIDEgNi44MzMtMy45NDkgMi40OCAyLjQ4IDAgMCAxIDIuOTA2IDEuMTNsMS4wMjIgMS43ODZjLjQ2LS4wNDMuOTIyLS4wNjUgMS4zODQtLjA2NHYtNS4xODJjLTEuMzc0LS4wMTEtMi43NTEtLjAwMS00LjEyNy0uMDA1di0zLjY5NGgtMi41ODZ2LTMuNjk0aC0xLjkwN2MtLjAwNC0yLjQ2MiAwLTQuOTI1IDAtNy4zODhoLTIuMjc4djcuMzg4Yy0uNjM3LS4wMDItMS4yNzQgMC0xLjkxMS4wMDUuMDAyIDEuMjI5LjAwNCAyLjQ1OSAwIDMuNjg4LS44ODMuMDAyLTEuNzY1IDAtMi42NDYuMDAxdjMuNjk0aC00LjA2M3Y1NC41ODZoMTkuNTJjLS4wMDItMy4yOC0uMDAzLTExLjYyNS0uMDAzLTIwLjkwNC0uNDU4IDAtLjkxNi0uMDIyLTEuMzcyLS4wNjRsLTEuMDIyIDEuNzc2Wm05LjMzLTE1Ljk2YzAtMy44MjktMy4xMTctNi45MzctNi45MzUtNi45NDF2My40NDRjMS45MjQuMDAzIDMuNDkyIDEuNTczIDMuNDkyIDMuNDk3cy0xLjU2OCAzLjQ5NC0zLjQ5MiAzLjQ5N3YzLjQ0NGMzLjgxOC0uMDAzIDYuOTM2LTMuMTEyIDYuOTM2LTYuOTQxWm0xMC41MzUtMy45MzlhMi41IDIuNSAwIDAgMC0yLjQ0My0xLjk1OWgtMi4wNDVjLS4zNzktLjg0LS44NC0xLjY0LTEuMzc3LTIuMzg5bDEuMDIyLTEuNzc2YTIuNTA2IDIuNTA2IDAgMCAwLS40NzMtMy4wODggMTguMTMxIDE4LjEzMSAwIDAgMC02LjgyMy0zLjk0OSAyLjUzIDIuNTMgMCAwIDAtMi45MzggMS4xNDFsLTEuMDIyIDEuNzc2YTE0LjU3NCAxNC41NzQgMCAwIDAtMS4zNy0uMDY0djMuNDM0Yy44MjMuMDAzIDEuNjgzLjEzNSAzLjE2OC40MDdsMS44MjktMy4xNjRhMTQuMjQ0IDE0LjI0NCAwIDAgMSA0LjI1MSAyLjQ1NGwtMS44MjkgMy4xNjRjMS45NjkgMi4zMDMgMi4xNjMgMi42MzYgMy4xNzUgNS40OTloMy42NTljLjI4IDEuNjI1LjI4IDMuMjkzIDAgNC45MDdIODIuOTZjLTEuMDIyIDIuODk1LTEuMjU5IDMuMjUtMy4xNzUgNS40OTlsMS44MjkgMy4xNjRhMTQuMzY3IDE0LjM2NyAwIDAgMS00LjI1MSAyLjQ1NGwtMS44MjktMy4xNjRjLTEuNDc2LjI3LTIuMzAzLjQxLTMuMTY5LjQwN3YzLjQzNGMuNDYyIDAgLjkyNC0uMDIxIDEuMzgzLS4wNjRsMS4wMjIgMS43ODZjLjU4MSAxLjAwMSAxLjgxOSAxLjQ4NSAyLjkxNiAxLjEzYTE3LjgxNSAxNy44MTUgMCAwIDAgNi44MzMtMy45NDkgMi41IDIuNSAwIDAgMCAuNDczLTMuMDg4bC0xLjAyMi0xLjc3NmMuNTM3LS43NDkuOTk5LTEuNTQ5IDEuMzc3LTIuMzg5aDIuMDQ1YTIuNDg4IDIuNDg4IDAgMCAwIDIuNDQzLTEuOTU5Yy4yOTEtMS4yOTEuNDMtMi42MTUuNDMtMy45MzlzLS4xNC0yLjY1OC0uNDMtMy45MzlaIi8+PC9zdmc+DQo="
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
        description: "Creating and Accessing Aliases for Runs"
      },
      {
        name: "Model",
        description: "Creating, and Downloading Models"
      },
      {
        name: "Run",
        description: "Creating, Interacting, and Destroying Runs"
      },
      {
        name: "Point",
        description: "Reading, Writing, and Listing Points"
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
        tags: ["About", "Model", "Run", "Point", "Alias"]
      },
      {
        name: "Project Haystack API",
        tags: ["Haystack"]
      }
    ]
  }
});

mkdirp.sync("build/app/assets");
fs.writeFileSync("build/app/openapi.json", JSON.stringify(openapiSpecification));

npmRun.execSync("redocly build-docs openapi.json -t ../../docs.hbs", { cwd: __dirname + "/build/app" });
