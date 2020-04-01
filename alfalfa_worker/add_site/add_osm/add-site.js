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

// Given a haystack.json file, add a new site to the haystack mongo database
// The alfalfa_worker is mostly python, but since we want to use the functions in nodehaystack
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

MongoClient.connect(process.env.MONGO_URL).then((client) => {
  db = client.db(process.env.MONGO_DB_NAME);
  mrecs = db.collection('recs');
  addFile(process.argv[2],process.argv[3]);
}).catch((err) => {
  console.log(err);
  process.exit(1);
});
