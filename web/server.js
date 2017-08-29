
// Module dependencies.
import path from 'path';
import hs from 'nodehaystack';
import express from 'express';
import url from 'url';
import bodyParser from 'body-parser';
import alfalfaServer from './alfalfa-server';
import {MongoClient} from 'mongodb';
import graphQLHTTP from 'express-graphql';
import {Schema} from './schema';
import historyApiFallback from 'connect-history-api-fallback';
import morgan from 'morgan';

var app = express();

app.use(morgan('combined'))

app.use(bodyParser.text({ type: 'text/*' }));
app.use(bodyParser.json()); // if you are using JSON instead of ZINC you need this

app.use('/graphql', graphQLHTTP({
  graphiql: true,
  pretty: true,
  schema: Schema,
}));

app.all('/api/*', function(req, res) {
  // Remove this in production
  console.log('body: ', req.body);

  var path = url.parse(req.url).pathname;
  path = path.replace('/api','');

  // parse URI path into "/{opName}/...."
  var slash = path.indexOf('/', 1);
  if (slash < 0) slash = path.length;
  var opName = path.substring(1, slash);


  // resolve the op
  app.locals.alfalfaServer.op(opName, false, function(err, op) {
    if (typeof(op) === 'undefined' || op === null) {
      res.status(404);
      res.send("404 Not Found");
      res.end();
      return;
    }

    // route to the op
    op.onServiceOp(app.locals.alfalfaServer, req, res, function(err) {
      if (err) {
        console.log(err.stack);
        throw err;
      }
      res.end();
    });
  });
});

app.use(historyApiFallback());
app.use('/', express.static(path.join(__dirname, './build')));

MongoClient.connect(process.env.MONGO_URL).then((db) => {
  app.locals.alfalfaServer = new alfalfaServer(db);
  let server = app.listen(80, () => {
  
    var host = server.address().address;
    var port = server.address().port;
  
    if (host.length === 0 || host === "::") host = "localhost";
  
    console.log('Node Haystack Toolkit listening at http://%s:%s', host, port);
  
  });
}).catch((err) => {
  console.log(err);
});

