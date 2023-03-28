const fs = require("node:fs");
if (fs.existsSync("../.env")) require("dotenv").config({ path: "../.env" });

const isProd = process.env.NODE_ENV === "production";

const presets = [
  "@babel/preset-react",
  [
    "@babel/preset-env",
    {
      corejs: "3.29",
      useBuiltIns: "usage"
    }
  ]
];

if (isProd) presets.push(["minify", { builtIns: false }]);

module.exports = {
  assumptions: {
    noDocumentAll: true,
    noClassCalls: true
  },
  comments: false,
  plugins: ["@babel/plugin-proposal-class-properties"],
  presets,
  sourceMaps: isProd ? false : "inline"
};
