
// Given a haystack.json file, add a new site to the haystack mongo database
// The worker is mostly python, but since we want to use the functions in nodehaystack
// this task is done with node

import os from 'os';
import fs from 'fs';
import hs from 'nodehaystack';
import HDict from 'nodehaystack/HDict';
import {MongoClient} from 'mongodb';

var HBool = hs.HBool,
    HDateTime = hs.HDateTime,
    HDictBuilder = hs.HDictBuilder,
    HGrid = hs.HGrid,
    HHisItem = hs.HHisItem,
    HMarker = hs.HMarker,
    HNum = hs.HNum,
    HRef = hs.HRef,
    HStr = hs.HStr,
    HUri = hs.HUri,
    HGridBuilder = hs.HGridBuilder,
    HServer = hs.HServer,
    HStdOps = hs.HStdOps,
    HJsonReader = hs.HJsonReader;

console.log('Add site from: ', process.argv[2]);

let db = null;
let mrecs = null;

function addFile(json_file, site_ref) {
  fs.readFile(json_file, 'utf8', (err, data) => {
      if (err) {
        console.log('Error parsing json points file: ',err); 
      } else {
        try {
          let recs = JSON.parse(data);
          let array = recs.map((rec) => {
            let reader = new HJsonReader(rec.id)
            let id = reader.readScalar().val;
            return {
              _id: id,
              site_ref: site_ref,
              rec: rec
            };
          });
          mrecs.insertMany(array).then(() => {
            process.exit(0);
          }).catch((err) => {
            console.log(err);
            process.exit(0);
          });
        } catch(err) {
          console.log(err);
          process.exit(0);
        }
      }
  });
}

MongoClient.connect(process.env.MONGO_URL).then((_db) => {
  db = _db;
  mrecs = db.collection('recs');
  addFile(process.argv[2],process.argv[3]);
}).catch((err) => {
  console.log(err);
  process.exit(1);
});


