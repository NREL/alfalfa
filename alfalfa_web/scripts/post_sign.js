const crypto = require("crypto-js");

const policy = {
  expiration: "2050-01-01T12:00:00.000Z",
  conditions: [
    { bucket: process.env.S3_BUCKET },
    { acl: "private" },
    { "x-amz-credential": "AKIAIJ3WS3HZDVQG676Q/20500101/us-west-1/s3/aws4_request" },
    { "x-amz-algorithm": "AWS4-HMAC-SHA256" },
    { "x-amz-date": "20500101T000000Z" },
    ["starts-with", "$key", "uploads"],
    ["content-length-range", 0, 10485760]
  ]
};

function getSignatureKey(key, dateStamp, regionName, serviceName) {
  const kDate = crypto.HmacSHA256(dateStamp, "AWS4" + key);
  const kRegion = crypto.HmacSHA256(regionName, kDate);
  const kService = crypto.HmacSHA256(serviceName, kRegion);
  const kSigning = crypto.HmacSHA256("aws4_request", kService);
  return kSigning;
}

const key = getSignatureKey(process.env.AWS_SECRET_ACCESS_KEY, "20500101", "us-west-1", "s3");
const base64Policy = new Buffer(JSON.stringify(policy), "utf-8").toString("base64");
const sig = crypto.HmacSHA256(base64Policy, key).toString(crypto.enc.Hex);

console.log("base64Policy:", base64Policy);
console.log("signature:", sig.toString(crypto.enc.Hex));
