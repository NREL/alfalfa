
// Module dependencies.
var hs = require('nodehaystack'),
    express = require('express'),
    url = require('url'),
    bodyParser = require('body-parser'),
    db = require('./database');

var app = express();
db = new db();

app.use(bodyParser.text({ type: 'text/*' }));
app.use(bodyParser.json()); // if you are using JSON instead of ZINC you need this

app.all('*', function(req, res) {
  var path = url.parse(req.url).pathname;

  // if root, then redirect to {haystack}/about
  if (typeof(path) === 'undefined' || path === null || path.length === 0 || path === "/") {
    res.redirect("/about");
    return;
  }

  // parse URI path into "/{opName}/...."
  var slash = path.indexOf('/', 1);
  if (slash < 0) slash = path.length;
  var opName = path.substring(1, slash);

  // resolve the op
  db.op(opName, false, function(err, op) {
    if (typeof(op) === 'undefined' || op === null) {
      res.status(404);
      res.send("404 Not Found");
      res.end();
      return;
    }

    // route to the op
    op.onServiceOp(db, req, res, function(err) {
      if (err) {
        console.log(err.stack);
        throw err;
      }

      res.end();
    });
  });
});

var server = app.listen(3000, function() {

  var host = server.address().address;
  var port = server.address().port;

  if (host.length === 0 || host === "::") host = "localhost";

  console.log('Node Haystack Toolkit listening at http://%s:%s', host, port);

});

