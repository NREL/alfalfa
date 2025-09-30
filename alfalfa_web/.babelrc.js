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

// Use Webpack's built-in Terser for minification instead of babel-preset-minify
// which has compatibility issues with newer Babel versions

module.exports = {
  assumptions: {
    noDocumentAll: true,
    noClassCalls: true
  },
  comments: false,
  plugins: ["@babel/plugin-transform-class-properties"],
  presets,
  sourceMaps: isProd ? false : "inline"
};
