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

function sitePointResolver(siteRef) {
  return new Promise( (resolve,reject) => {
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
          "filter": `s:point and siteRef==@${siteRef}`,
        }
      ]
    })
    .end((err, res) => {
      if( err ) {
        reject(err);
      } else {
        let points = [];
        let dis = 'Haystack Point';
        res.body.rows.map( (row) => {
          let tags = [];
          Object.keys(row).map((key) => {
            if( key == 'dis' ) {
              dis = row[key];
              if( dis ) {
                dis = dis.replace(/[a-z]\:/,'');
              }
            }
            let tag = {
              key: key,
              value: row[key]
            };
            tags.push(tag);
          });
          //let site = {
          //  name: row.dis.replace(/[a-z]\:/,''),
          //  siteRef: row.id.replace(/[a-z]\:/,''),
          //  simStatus: 'Stopped',
          //};
          let point = {
            dis: dis,
            tags: tags
          };
          points.push(point);
        });
        resolve(points);
      }
    })
  });
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

module.exports = { addJobResolver, sitesResolver, startSimulationResolver, sitePointResolver };

