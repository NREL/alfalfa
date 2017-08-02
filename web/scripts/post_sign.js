const crypto = require("crypto-js");
const Base64 = require('crypto-js/enc-base64');
const Hex = require('crypto-js/enc-hex');

const policy = {"expiration": "2050-01-01T12:00:00.000Z",
 "conditions": [
   {"bucket": "alfalfa"},
   {"acl": "private"},
   {"x-amz-credential": "AKIAJQLYQJ5ISJVPU7IQ/20500101/us-west-1/s3/aws4_request"},
   {"x-amz-algorithm": "AWS4-HMAC-SHA256"},
   {"x-amz-date": "20500101T000000Z" },
   ["starts-with", "$key", "uploads"],
   ["content-length-range", 0, 10485760]
 ]}

function getSignatureKey(key, dateStamp, regionName, serviceName) {
    var kDate = crypto.HmacSHA256(dateStamp, "AWS4" + key);
    var kRegion = crypto.HmacSHA256(regionName, kDate);
    var kService = crypto.HmacSHA256(serviceName, kRegion);
    var kSigning = crypto.HmacSHA256("aws4_request", kService);
    return kSigning;
};

const key = getSignatureKey('uPVKkLJoqoOeT3GMVGQnyE2ztcmjZ4WGt9iwmQ5r','20500101','us-west-1','s3');
const base64Policy = new Buffer(JSON.stringify(policy), "utf-8").toString("base64");
const sig = crypto.HmacSHA256(base64Policy,key).toString(crypto.enc.Hex);

console.log('base64Policy:', base64Policy);
console.log('signature:', sig.toString(crypto.enc.Hex));
