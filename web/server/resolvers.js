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

import AWS from 'aws-sdk';
import request from 'superagent';
import {MongoClient} from 'mongodb';
import path from 'path';
import dbops from './dbops';

AWS.config.update({region: process.env.REGION});
var sqs = new AWS.SQS();
var s3client = new AWS.S3({endpoint: process.env.S3_URL});

function addSiteResolver(osmName, uploadID) {
  var params = {
   MessageBody: `{"op": "InvokeAction", 
      "action": "addSite", 
      "osm_name": "${osmName}", 
      "upload_id": "${uploadID}"
    }`,
   QueueUrl: process.env.JOB_QUEUE_URL,
   MessageGroupId: "Alfalfa"
  };
  
  sqs.sendMessage(params, (err, data) => {
    if (err) {
      console.log(err);
      callback(err);
    }
  });
}

function runSimResolver(uploadFilename, uploadID, context) {
  var params = {
   MessageBody: `{"op": "InvokeAction", 
    "action": "runSim", 
    "upload_filename": "${uploadFilename}", 
    "upload_id": "${uploadID}"
   }`,
   QueueUrl: process.env.JOB_QUEUE_URL,
   MessageGroupId: "Alfalfa"
  };
  
  sqs.sendMessage(params, (err, data) => {
    if (err) {
      callback(err);
    } else {
      const simcollection = context.db.collection('sims');
      simcollection.insert( {_id: uploadID, siteRef: uploadID, simStatus: "Queued", name: path.parse(uploadFilename).name.replace(".tar","") } );
    }
  });
}

function runSiteResolver(args) {
    //args: {
    //  siteRef : { type: new GraphQLNonNull(GraphQLString) },
    //  startDatetime : { type: GraphQLString },
    //  endDatetime : { type: GraphQLString },
    //  timescale : { type: GraphQLFloat },
    //  realtime : { type: GraphQLBoolean },
    //  externalClock : { type: GraphQLBoolean },
    //},
  console.log("args: ", args)
  return new Promise( (resolve,reject) => {
    request
    .post('/api/invokeAction')
    .set('Accept', 'application/json')
    .set('Content-Type', 'application/json')
    .send({
      "meta": {
        "ver": "2.0",
        "id": `r:${args.siteRef}`,
        "action": "s:runSite"
      },
      "cols": [
        {
          "name": "timescale"
        },
        {
          "name": "startDatetime"
        },
        {
          "name": "endDatetime"
        },
        {
          "name": "realtime"
        },
        {
          "name": "externalClock"
        },
      ],
      "rows": [
        {
          "timescale": `s:${args.timescale}`,
          "startDatetime": `s:${args.startDatetime}`,
          "endDatetime": `s:${args.endDatetime}`,
          "realtime": `s:${args.realtime}`,
          "externalClock": `s:${args.externalClock}`,
        }
      ]
    })
    .end((err, res) => {
      if( err ) {
        reject(err);
      } else {
        resolve(res.body);
      }
    })
  });
}

function stopSiteResolver(args) {
      //args: {
      //  siteRef : { type: new GraphQLNonNull(GraphQLString) },
      //},
  return new Promise( (resolve,reject) => {
    request
    .post('/api/invokeAction')
    .set('Accept', 'application/json')
    .set('Content-Type', 'application/json')
    .send({
      "meta": {
        "ver": "2.0",
        "id": `r:${args.siteRef}`,
        "action": "s:stopSite"
      },
      "cols": [
        {
          "name": "foo" // because node Haystack craps out if there are no columns
        },
      ],
      "rows": [
        {
          "foo": "s:bar",
        }
      ]
    })
    .end((err, res) => {
      if( err ) {
        reject(err);
      } else {
        resolve(res.body);
      }
    })
  });
}

function removeSiteResolver(args) {
      //args: {
      //  siteRef : { type: new GraphQLNonNull(GraphQLString) },
      //},
  return new Promise( (resolve,reject) => {
    request
    .post('/api/invokeAction')
    .set('Accept', 'application/json')
    .set('Content-Type', 'application/json')
    .send({
      "meta": {
        "ver": "2.0",
        "id": `r:${args.siteRef}`,
        "action": "s:removeSite"
      },
      "cols": [
        {
          "name": "foo" // because node Haystack craps out if there are no columns
        },
      ],
      "rows": [
        {
          "foo": "s:bar",
        }
      ]
    })
    .end((err, res) => {
      if( err ) {
        reject(err);
      } else {
        resolve(res.body);
      }
    })
  });
}

function  simsResolver(user,args,context) {
  return new Promise( (resolve,reject) => {
      let sims = [];
      const simcollection = context.db.collection('sims');
      simcollection.find(args).toArray().then((array) => {
        array.map( (sim) => {
          sim = (Object.assign(sim, {"simRef": sim._id}));
          if ( sim.s3Key ) {
            var params = {Bucket: process.env.S3_BUCKET, Key: sim.s3Key, Expires: 86400};
            var url = s3client.getSignedUrl('getObject', params);
            sim = (Object.assign(sim, {"url": url}));
          }
          sims.push(sim)
        })
        resolve(sims);
      }).catch((err) => {
        reject(err);
      });
    });
};

function  sitesResolver(user,siteRef) {
  let filter = "s:site";
  if( siteRef ) {
    filter = `${filter} and id==@${siteRef}`;
  }
  return new Promise( (resolve,reject) => {
    let sites = [];
    request
    .post('/api/read')
    .set('Accept', 'application/json')
    .send({
      "meta": {
        "ver": "2.0"
      },
      "cols": [
        {
          "name": "filter"
        }
      ],
      "rows": [
        {
          "filter": filter,
        }
      ]
    })
    .end((err, res) => {
      if( err ) {
        reject(err);
      } else {
        res.body.rows.map( (row) => {
          let site = {
            name: row.dis.replace(/[a-z]\:/,''),
            siteRef: row.id.replace(/[a-z]\:/,''),
            simStatus: row.simStatus.replace(/[a-z]\:/,''),
            simType: row.simType.replace(/[a-z]\:/,''),
          };
          let datetime = row['datetime'];
          if( datetime ) {
            datetime = datetime.replace(/[a-z]\:/,'');
            site.datetime = datetime;
          }

          let step = row['step'];
          if (step){
            step=step.replace(/[a-z]\:/, '');
            site.step=step;
          }

          sites.push(site);
        });
        resolve(sites);
      }
    })
  });
}

function sitePointResolver(siteRef, args, context) {
  return new Promise((resolve, reject) => {
    const recs = context.db.collection('recs');
    let query = {site_ref: siteRef, "rec.point": "m:"};
    if (args.writable) {query["rec.writable"] = "m:"};
    if (args.cur) {query["rec.cur"] = "m:"};
    recs.find(query).toArray().then((array) => {
      let points = [];
      array.map( (rec) => {
        let point = {};
        point.tags = [];
        point.dis = rec.rec.dis
        for (const reckey in rec.rec) {
            const tag = {key: reckey, value: rec.rec[reckey]};
            point.tags.push(tag);
        }
        points.push(point);
      });
      resolve(points)
    }).catch((err) => {
      reject(err);
    });
  });
}

function advanceResolver(advancer, siteRef) {
  return advancer.advance(siteRef);
}

function writePointResolver(context,siteRef, pointName, value, level) {
  return dbops.getPoint(siteRef, pointName, context.db).then( point => {
    return dbops.writePoint(point._id, siteRef, level, value, null, null, context.db);
  }).then( array => {
    return array;
  });
}

module.exports = { 
  runSimResolver, 
  addSiteResolver, 
  sitesResolver, 
  runSiteResolver, 
  stopSiteResolver, 
  removeSiteResolver, 
  sitePointResolver, 
  simsResolver, 
  advanceResolver,
  writePointResolver 
};

