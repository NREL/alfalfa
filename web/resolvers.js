import AWS from 'aws-sdk';
AWS.config.update({region: 'us-west-1'});
var sqs = new AWS.SQS();

function addJobResolver(fileName) {
  var params = {
   MessageBody: `{"op": "InvokeAction", "action": "add_site", "site_name": "${fileName}"}`,
   QueueUrl: process.env.JOB_QUEUE_URL
  };
  
  sqs.sendMessage(params, (err, data) => {
    if (err) {
      callback(err);
    }
  });
}

module.exports = { addJobResolver };
