// The purpose of this file is to consolidate operations to the database
// in a single place. Clients may transform the data into and out of
// these functions for their own api purposes. ie Haystack api, GraphQL api.

import { getPointKey, mapRedisArray } from "./utils";

const NUM_LEVELS = 17;

function findCurrentWinningValue(array) {
  for (let i = 0; i < NUM_LEVELS; ++i) {
    const val = array[i];
    if (val !== null) {
      return {
        val,
        level: i + 1
      };
    }
  }

  return null;
}

// Get a point by siteRef and display name
function getPoint(siteRef, name, db) {
  const mrecs = db.collection("recs");
  return mrecs.findOne({ "rec.siteRef": `r:${siteRef}`, "rec.dis": `s:${name}` });
}

async function getWriteArray(siteRef, id, redis) {
  const key = getPointKey(siteRef, id);
  return new Promise((resolve, reject) => {
    // If the key isn't set the array will be empty
    redis.lrange(key, 0, -1, (err, array) =>
      err ? reject(err) : resolve(array.length ? mapRedisArray(array) : undefined)
    );
  });
}

function writePoint(id, siteRef, level, value, db, redis) {
  return new Promise(async (resolve, reject) => {
    const key = getPointKey(siteRef, id);
    const mrecs = db.collection("recs");

    if (!Number.isInteger(level) || level < 1 || level > NUM_LEVELS) {
      level = 17;
    }

    try {
      let array = await getWriteArray(siteRef, id, redis);

      let currentWinningValue;
      if (array) {
        // Update
        array[level - 1] = value;
        await new Promise((resolve, reject) => {
          redis.lset(key, level - 1, value, (err, result) => (!err && result === "OK" ? resolve() : reject(err)));
        });
        currentWinningValue = findCurrentWinningValue(array);
      } else {
        // Insert
        await new Promise((resolve, reject) => {
          array = new Array(NUM_LEVELS).fill("");
          array[level - 1] = value;
          redis.rpush(key, array, (err, result) => {
            if (err) return reject(err);
            if (result === NUM_LEVELS) return resolve();
            else return reject(`Unexpected RPUSH result: ${result}`);
          });
          array = mapRedisArray(array);
        });
        currentWinningValue = {
          val: value,
          level
        };
      }

      if (currentWinningValue) {
        await mrecs.updateOne(
          { ref_id: id },
          {
            $set: {
              "rec.writeStatus": "s:ok",
              "rec.writeVal": `n:${currentWinningValue.val}`,
              "rec.writeLevel": `n:${currentWinningValue.level}`
            },
            $unset: {
              "rec.writeErr": ""
            }
          }
        );
      } else {
        // In this case the point has never been written to and there is no
        // existing writearray in the db, so error out. A default writearray
        // should have been created when the rec was created on the backend.
        console.error("No writearrary found for point " + id + ". Make sure it exists in the original tag file.");
      }

      resolve({
        ref_id: id,
        siteRef,
        val: array,
        who: new Array(NUM_LEVELS).fill(null)
      });
    } catch (err) {
      reject(err);
    }
  });
}

module.exports = {
  NUM_LEVELS,
  getPoint,
  getWriteArray,
  writePoint
};
