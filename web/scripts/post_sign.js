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

const crypto = require("crypto-js");
const Base64 = require('crypto-js/enc-base64');
const Hex = require('crypto-js/enc-hex');

const policy = {"expiration": "2050-01-01T12:00:00.000Z",
 "conditions": [
   {"bucket": process.env.S3_BUCKET},
   {"acl": "private"},
   {"x-amz-credential": "AKIAIJ3WS3HZDVQG676Q/20500101/us-west-1/s3/aws4_request"},
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

const key = getSignatureKey(process.env.AWS_SECRET_ACCESS_KEY,'20500101','us-west-1','s3');
const base64Policy = new Buffer(JSON.stringify(policy), "utf-8").toString("base64");
const sig = crypto.HmacSHA256(base64Policy,key).toString(crypto.enc.Hex);

console.log('base64Policy:', base64Policy);
console.log('signature:', sig.toString(crypto.enc.Hex));

