const fs = require("fs");
if (fs.existsSync("../.env")) require("dotenv").config({ path: "../.env" });

const path = require("path");
const HtmlWebpackPlugin = require("html-webpack-plugin");
const TerserPlugin = require("terser-webpack-plugin");

const isProd = process.env.NODE_ENV === "production";

module.exports = {
  mode: isProd ? "production" : "development",
  devtool: isProd ? false : "source-map",
  entry: "./app.js",
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
  plugins: [new HtmlWebpackPlugin({ template: "./index.html" })]
};
