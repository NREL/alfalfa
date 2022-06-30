/***********************************************************************************************************************
 *  Copyright (c) 2008-2022, Alliance for Sustainable Energy, LLC, and other contributors. All rights reserved.
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

// The purpose of this file is to consolidate operations to the database
// in a single place. Clients may transform the data into and out of
// these functions for their own api purposes. ie Haystack api, GraphQL api.

class WriteArray {
  constructor() {
    this.val = [];
    this.who = [];

    for (let i = 0; i < 17; ++i) {
      this.val[i] = null;
      this.who[i] = null;
    }
  }
}

function currentWinningValue(array) {
  for (let i = 0; i < array.val.length; ++i) {
    const v = array.val[i];
    if (v || v === 0) {
      return {
        val: v,
        level: i + 1
      };
    }
  }

  return null;
}

function setOrNullArray(array, val, level, who) {
  if (val || val === 0) {
    array.val[level - 1] = val;
    array.who[level - 1] = who;
  } else {
    array.val[level - 1] = null;
    array.who[level - 1] = null;
  }
}

// Get a point by siteRef and display name
function getPoint(siteRef, name, db) {
  const mrecs = db.collection("recs");
  return mrecs.findOne({ site_ref: siteRef, "rec.dis": `s:${name}` });
}

function writePoint(id, siteRef, level, val, who, dur, db) {
  return new Promise((resolve, reject) => {
    const writearrays = db.collection("writearrays");
    const mrecs = db.collection("recs");

    if (!level) {
      level = 1;
    }

    writearrays
      .findOne({ _id: id })
      .then((array) => {
        if (array) {
          // In this case the array already exists because it has been written to before
          setOrNullArray(array, val, level, who);
          writearrays
            .updateOne({ _id: array._id }, { $set: { val: array.val, who: array.who } })
            .then(() => {
              const current = currentWinningValue(array);
              if (current) {
                return mrecs.updateOne(
                  { _id: array._id },
                  {
                    $set: {
                      "rec.writeStatus": "s:ok",
                      "rec.writeVal": `s:${current.val}`,
                      "rec.writeLevel": `n:${current.level}`
                    },
                    $unset: { writeErr: "" }
                  }
                );
              } else {
                return mrecs.updateOne(
                  { _id: array._id },
                  {
                    $set: { "rec.writeStatus": "s:disabled" },
                    $unset: { "rec.writeVal": "", "rec.writeLevel": "", "rec.writeErr": "" }
                  }
                );
              }
            })
            .then(() => {
              resolve(array);
            })
            .catch((err) => {
              reject(err);
            });
        } else {
          // In this case the point has never been written to and there is no
          // existing write array in the db so we create a new one
          let array = new WriteArray();
          array._id = id;
          array.siteRef = siteRef;
          setOrNullArray(array, val, level, who);
          writearrays
            .insertOne(array)
            .then(() => {
              const current = currentWinningValue(array);
              if (current) {
                return mrecs.updateOne(
                  { _id: array._id },
                  {
                    $set: {
                      "rec.writeStatus": "s:ok",
                      "rec.writeVal": `s:${current.val}`,
                      "rec.writeLevel": `n:${current.level}`
                    },
                    $unset: { writeErr: "" }
                  }
                );
              } else {
                return mrecs.updateOne(
                  { _id: array._id },
                  {
                    $set: { "rec.writeStatus": "s:disabled" },
                    $unset: { "rec.writeVal": "", "rec.writeLevel": "", "rec.writeErr": "" }
                  }
                );
              }
            })
            .then(() => {
              resolve(array);
            })
            .catch((err) => {
              reject(err);
            });
        }
      })
      .catch((err) => {
        reject(err);
      });
  });
}

module.exports = { writePoint, getPoint };
