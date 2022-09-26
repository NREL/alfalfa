// Delete multiple redis keys
function del(client, keys) {
  return new Promise((resolve, reject) => {
    client.del(keys, (err, result) => {
      if (err) return reject(err);
      return resolve(result);
    });
  });
}

// Return all properties from a redis hash
function getHash(client, key) {
  return new Promise((resolve, reject) => {
    client.hgetall(key, (err, result) => (err ? reject(err) : resolve(result)));
  });
}

// Given a siteRef and pointId return the redis key
function getPointKey(siteRef, pointId) {
  return `site:${siteRef}:point:${pointId}`;
}

// Convert redis empty strings to nulls, otherwise numbers
function mapRedisArray(array) {
  return array.map((datum) => (datum === "" ? null : Number(datum)));
}

// Find all redis keys matching a wildcard pattern
function scan(client, pattern, cursor = "0", keys = []) {
  return new Promise((resolve, reject) => {
    client.scan(cursor, "MATCH", pattern, "COUNT", "10", async (err, result) => {
      if (err) return reject(err);
      cursor = result[0];
      keys = keys.concat(result[1]);

      if (cursor === "0") {
        return resolve(keys.sort());
      }
      keys = await scan(client, pattern, cursor, keys);
      return resolve(keys);
    });
  });
}

module.exports = {
  del,
  getHash,
  getPointKey,
  mapRedisArray,
  scan
};
