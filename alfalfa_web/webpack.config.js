const fs = require("node:fs");
if (fs.existsSync("../.env")) require("dotenv").config({ path: "../.env" });

const path = require("node:path");
const WebpackBeforeBuildPlugin = require("before-build-webpack");
const CopyPlugin = require("copy-webpack-plugin");
const HtmlWebpackPlugin = require("html-webpack-plugin");
const npmRun = require("npm-run");
const TerserPlugin = require("terser-webpack-plugin");

const isProd = process.env.NODE_ENV === "production";

const getSha = () => {
  let sha = process.env.GIT_COMMIT;
  if (!sha) {
    try {
      sha = npmRun.execSync("git rev-parse HEAD", { cwd: __dirname }).toString().trim().substring(0, 7);
    } catch (e) {
      console.error("Failed to determine git sha");
    }
  }
  fs.writeFileSync(path.resolve(__dirname, "build", "sha.json"), JSON.stringify({ sha }));
};

module.exports = {
  mode: isProd ? "production" : "development",
  devtool: isProd ? false : "source-map",
  entry: "./app.js",
  cache: {
    type: "filesystem"
  },
  devServer: {
    static: {
      directory: path.join(__dirname, "public")
    },
    compress: true,
    port: 80
  },
  watchOptions: {
    ignored: ["**/node_modules", "**/scripts", "**/server"]
  },
  output: {
    path: path.resolve(__dirname, "build/app"),
    filename: "app.bundle.js"
  },
  optimization: {
    minimize: isProd,
    minimizer: [
      new TerserPlugin({
        terserOptions: {
          mangle: true
        }
      })
    ]
  },
  module: {
    rules: [
      {
        test: /\.m?js$/,
        exclude: /node_modules/,
        use: "babel-loader"
      },
      {
        test: /\.s?css$/i,
        use: [
          "style-loader",
          {
            loader: "css-loader",
            options: {
              modules: true
            }
          },
          {
            loader: "postcss-loader",
            options: {
              postcssOptions: {
                plugins: ["postcss-preset-env"]
              }
            }
          },
          "sass-loader"
        ]
      },
      {
        test: /\.woff2?$/i,
        type: "asset/resource",
        generator: {
          filename: "assets/[name]-[hash][ext]"
        }
      }
    ]
  },
  plugins: [
    new WebpackBeforeBuildPlugin((stats, callback) => {
      getSha();
      callback();
    }),
    new HtmlWebpackPlugin({ template: "./index.html" }),
    new CopyPlugin({
      patterns: [
        {
          from: "favicon.ico",
          to: "favicon.ico"
        }
      ]
    })
  ]
};
