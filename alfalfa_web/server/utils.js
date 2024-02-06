// Delete multiple redis keys
function del(client, keys) {
  return client.del(keys);
}

// Return the value of a specific property from a redis hash
function getHashValue(client, key, prop) {
  return client.hGet(key, prop);
}

// Return all properties from a redis hash
function getHash(client, key) {
  return client.hGetAll(key);
}

// Given a siteRef and pointId return the redis key
function getPointKey(siteRef, pointId) {
  return `run:${siteRef}:point:${pointId}`;
}

// Convert redis empty strings to nulls, otherwise numbers
function mapRedisArray(array) {
  return array.map((datum) => (datum === "" ? null : Number(datum)));
}

// Find all redis keys matching a wildcard pattern
async function scan(client, pattern) {
  const keys = [];
  for await (const key of client.scanIterator({ MATCH: pattern, COUNT: 100 })) {
    keys.push(key);
  }
  return keys;
}

function mapHaystack(obj) {
  if (obj == null) return null;
  return Object.keys(obj).reduce((result, key) => {
    if (Array.isArray(obj[key])) {
      result[key] = obj[key].map((record) => mapHaystack(record));
    } else if (typeof obj[key] === "string") {
      const isNumber = obj[key].startsWith("n:");
      if (isNumber) {
        result[key] = Number(obj[key].replace(/^[a-z]:/, ""));
      } else {
        result[key] = obj[key].replace(/^[a-z]:/, "");
      }
    } else {
      result[key] = obj[key].toString();
    }
    return result;
  }, {});
}

function reduceById(arr, obj) {
  return { ...arr, [obj._id]: obj };
}

function reduceByRefId(arr, obj) {
  return { ...arr, [obj.ref_id]: obj };
}

module.exports = {
  del,
  getHash,
  getHashValue,
  getPointKey,
  mapHaystack,
  mapRedisArray,
  reduceById,
  reduceByRefId,
  scan
};
