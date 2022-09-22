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
  return mrecs.findOne({ "rec.siteRef": `r:${siteRef}`, "rec.dis": `s:${name}` });
}

function writePoint(id, siteRef, level, val, who, dur, db) {
  return new Promise((resolve, reject) => {
    const writearrays = db.collection("writearrays");
    const mrecs = db.collection("recs");

    if (!level) {
      level = 1;
    }

    writearrays
      .findOne({ ref_id: id })
      .then((array) => {
        if (array) {
          // In this case the array already exists because it has been written to before
          setOrNullArray(array, val, level, who);
          writearrays
            .updateOne({ ref_id: array.ref_id }, { $set: { val: array.val, who: array.who } })
            .then(() => {
              const current = currentWinningValue(array);
              if (current) {
                // console.log("The array has values of " + JSON.stringify(array));
                return mrecs.updateOne(
                  { ref_id: array.ref_id },
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
                  { ref_id: array.ref_id },
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
          // existing writearray in the db, so error out. A default writearray
          // should have been created when the rec was created on the backend.
          console.log("No writearrary found for point " + id + ". Make sure it exists in the original tag file.");

          // code below needs to be removed
          let array = new WriteArray();
          array.ref_id = id;
          array.siteRef = siteRef;
          setOrNullArray(array, val, level, who);
          writearrays
            .insertOne(array)
            .then(() => {
              const current = currentWinningValue(array);
              if (current) {
                return mrecs.updateOne(
                  { ref_id: array.ref_id },
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
                  { ref_id: array.ref_id },
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
