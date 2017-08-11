import AWS from 'aws-sdk';
import request from 'superagent';

AWS.config.update({region: 'us-west-1'});
var sqs = new AWS.SQS();

function addJobResolver(osmName, uploadID) {
  var params = {
   MessageBody: `{"op": "InvokeAction", "action": "add_site", "osm_name": "${osmName}", "upload_id": "${uploadID}"}`,
   QueueUrl: process.env.JOB_QUEUE_URL
  };
  
  sqs.sendMessage(params, (err, data) => {
    if (err) {
      callback(err);
    }
  });
}

function  sitesResolver(user) {
  return new Promise( (resolve,reject) => {
    let sites = [];
    request
    .get('/api/nav')
    .set('Accept', 'application/json')
    .end((err, res) => {
      if( err ) {
        reject(err);
      } else {
        res.body.rows.map( (row) => {
          let site = {
            name: row.dis.replace(/[a-z]\:/,''),
            siteRef: row.id.replace(/[a-z]\:/,''),
            simStatus: 'Stopped',
          };
          sites.push(site);
        });
        resolve(sites);
      }
    })
  });

    //name: {
    //  type: GraphQLString,
    //  description: 'The name of the site, corresponding to the haystack siteRef display name'
    //},
    //siteRef: {
    //  type: GraphQLString,
    //  description: 'A unique identifier, corresponding to the haystack siteRef value'
    //},
    //simStatus: {
    //  type: GraphQLString,
    //  description: 'The status of the site simulation'
    //}
}

function startSimulationResolver(siteRef) {
  return new Promise( (resolve,reject) => {
    request
    .post('/api/invokeAction')
    .set('Accept', 'application/json')
    .set('Content-Type', 'application/json')
    .send({
      "meta": {
        "ver": "2.0",
        "id": `r:${siteRef}`,
        "action": "s:start_simulation"
      },
      "cols": [
        {
          "name": "foo"
        },
        {
          "name": "time_scale"
        }
      ],
      "rows": [
        {
          "foo": "s:bar",
          "time_scale": "s:50000"
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

module.exports = { addJobResolver, sitesResolver, startSimulationResolver };

