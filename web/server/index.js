/***********************************************************************************************************************
*  Copyright (c) 2008-2018, Alliance for Sustainable Energy, LLC, and other contributors. All rights reserved.
*
*  Redistribution and use in source and binary forms, with or without modification, are permitted provided that the
*  following conditions are met:
*
*  (1) Redistributions of source code must retain the above copyright notice, this list of conditions and the following
*  disclaimer.
*
*  (2) Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following
*  disclaimer in the documentation and/or other materials provided with the distribution.
*
*  (3) Neither the name of the copyright holder nor the names of any contributors may be used to endorse or promote products
*  derived from this software without specific prior written permission from the respective party.
*
*  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDER(S) AND ANY CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
*  INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
*  DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER(S), ANY CONTRIBUTORS, THE UNITED STATES GOVERNMENT, OR THE UNITED
*  STATES DEPARTMENT OF ENERGY, NOR ANY OF THEIR EMPLOYEES, BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
*  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
*  USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
*  STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
*  ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
***********************************************************************************************************************/

// Module dependencies.
import path from 'path';
import hs from 'nodehaystack';
import express from 'express';
import url from 'url';
import bodyParser from 'body-parser';
import alfalfaServer from './alfalfa-server';
import {MongoClient} from 'mongodb';
import node_redis from 'redis';
import graphQLHTTP from 'express-graphql';
import {Schema} from './schema';
import {Advancer} from './advancer';
import historyApiFallback from 'connect-history-api-fallback';
import morgan from 'morgan';
import * as Minio from 'minio';
import { URL } from "url";

const s3URL = new URL(process.env.S3_URL);

const client = new Minio.Client({
    endPoint: s3URL.hostname,
    port: parseInt(s3URL.port),
    useSSL: s3URL.protocol == 'https:',
    accessKey: process.env.AWS_ACCESS_KEY_ID,
    secretKey: process.env.AWS_SECRET_ACCESS_KEY,
    region: 'us-west-1'
});

const redis = node_redis.createClient({host: process.env.REDIS_HOST});
const pub = redis.duplicate();
const sub = redis.duplicate();
const advancer = new Advancer(redis, pub, sub);

MongoClient.connect(process.env.MONGO_URL).then((mongoClient) => {
  var app = express();
  
  if( process.env.NODE_ENV == "production" ) {
    app.get('*.js', function(req, res, next) {
      req.url = req.url + '.gz';
      res.set('Content-Encoding', 'gzip');
      res.set('Content-Type', 'text/javascript');
      next();
    });

    app.get('*.css', function(req, res, next) {
      req.url = req.url + '.gz';
      res.set('Content-Encoding', 'gzip');
      res.set('Content-Type', 'text/css');
      next();
    });
  } else {
    app.use(morgan('combined'))
  }

  const db = mongoClient.db('boptest');

  app.locals.alfalfaServer = new alfalfaServer(db, redis, pub, sub);

  app.use('/graphql', (request, response) => {
      return graphQLHTTP({
        graphiql: true,
        pretty: true,
        schema: Schema,
        context: {
          ...request,
          db,
          advancer
        }
      })(request,response)
    }
  );
  
  app.use(bodyParser.text({ type: 'text/*' }));
  app.use(bodyParser.json()); // if you are using JSON instead of ZINC you need this

  // Create a post url for file uploads
  // from a browser
  app.post('/upload-url', (req, res) => {
    // Construct a new postPolicy.
    var policy = client.newPostPolicy()
    // Set the object name my-objectname.
    policy.setKey(req.body.name);
    // Set the bucket to my-bucketname.
    policy.setBucket("alfalfa");
    
    var expires = new Date
    expires.setSeconds(24 * 60 * 60 * 10) // 10 days expiry.
    policy.setExpires(expires)
    client.presignedPostPolicy(policy, function(e, data) {
        if (e) throw e;
        if ( s3URL.hostname.indexOf("amazonaws") == -1 ) {
          if (req.hostname.indexOf("web") == -1 ) {
            const postURL = 'http://' + req.hostname + ':9000/alfalfa';
            data.postURL = postURL;
          } else {
            const postURL = 'http://minio:9000/alfalfa';
            data.postURL = postURL;
          }
        }
        res.send(JSON.stringify(data));
        res.end();
        return;
    })
  });
  
  app.all('/api/*', function(req, res) {
    // Remove this in production
    var path = url.parse(req.url).pathname;
    path = path.replace('/api','');
  
    // parse URI path into "/{opName}/...."
    var slash = path.indexOf('/', 1);
    if (slash < 0) slash = path.length;
    var opName = path.substring(1, slash);
  
  
    // resolve the op
    app.locals.alfalfaServer.op(opName, false, function(err, op) {
      if (typeof(op) === 'undefined' || op === null) {
        res.status(404);
        res.send("404 Not Found");
        res.end();
        return;
      }
  
      // route to the op
      op.onServiceOp(app.locals.alfalfaServer, req, res, function(err) {
        if (err) {
          console.log(err.stack);
          throw err;
        }
        res.end();
      });
    });
  });
  
  app.use(historyApiFallback());
  app.use('/', express.static(path.join(__dirname, './app')));

  let server = app.listen(80, () => {
  
    var host = server.address().address;
    var port = server.address().port;
  
    if (host.length === 0 || host === "::") host = "localhost";
  
    console.log('Node Haystack Toolkit listening at http://%s:%s', host, port);
  
  });
}).catch((err) => {
  console.log(err);
});

