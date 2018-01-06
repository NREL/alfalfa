'use strict';
const webpack = require('webpack');
const fs = require('fs');
const path = require('path');
//const autoprefixer = require('autoprefixer');
//const precss = require('precss');
const {graphql} = require('graphql');
const {introspectionQuery, printSchema} = require('graphql/utilities');
const HtmlWebpackPlugin = require('html-webpack-plugin');

const title = 'Alfalfa';
const template = './index.html';
let devtool = '';
let plugins = [];

if (process.env.NODE_ENV === 'production') {
  const CompressionPlugin = require('compression-webpack-plugin');

  plugins = [
    new webpack.DefinePlugin({
      'process.env.NODE_ENV': JSON.stringify(process.env.NODE_ENV || 'development')
    }),
    new webpack.optimize.DedupePlugin(),
    new webpack.optimize.UglifyJsPlugin({
      compress: {
        warnings: false,
      },
      output: {
        comments: false,
      },
    }),
    new webpack.optimize.AggressiveMergingPlugin(),
    new HtmlWebpackPlugin({
      title: title,
      template: template
    }),
    new CompressionPlugin({
      asset: "[path].gz[query]",
      algorithm: "gzip",
      test: /\.js$|\.css$|\.html$/,
      threshold: 10240,
      minRatio: 0.8
    })
  ];

  devtool = 'eval';
} else {
  plugins = [
    new HtmlWebpackPlugin({
      title: title,
      template: template
    }),
    new webpack.HotModuleReplacementPlugin()
  ];

  devtool = 'source-map';
}

module.exports = {
  entry: { 
    app: ["./app.js"]
  },
  output: {
    path: path.join(__dirname, 'build'),
    filename: 'app.bundle.js',
  },
  devtool: 'source-map',
  module: {
    rules: [
      {
        test: /\.js$/,
        exclude: /node_modules/,
        use: [{
          loader: 'babel-loader',
        }]
      },{
        test: /\.json$/,
        use: [{
            loader: "json"
        }]
      },{
        test: /\.(png|jpg|jpeg|gif|svg|woff|woff2)$/,
        use: [{
            loader: "url-loader?limit=10000&name=assets/[hash].[ext]"
        }]
      },{
        test: /\.css$/,
        use: [{
            loader: "style-loader" // creates style nodes from JS strings
        }, {
            loader: "css-loader" // translates CSS into CommonJS
        }]
      },{
        test: /\.scss$/,
        use: [{
            loader: "style-loader", // creates style nodes from JS strings
        }, {
            loader: "css-loader", // translates CSS into CommonJS
            options: {
              importLoaders: 1,
              modules: 1,
              localIdentName: '[name]__[local]___[hash:base64:5]'
            }
        }, {
            loader: "postcss-loader"
        }]
      }
    ]
  },
  plugins
}

