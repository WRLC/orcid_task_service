// server.js

var express = require('express'),
  app = express(),
  router = express.Router(),
  bodyParser = require('body-parser'),
  mongoose = require('mongoose'),
  config = require('./config'),
  Researcher = require('./app/models/researcher');

// set up mongodb
mongoose.Promise = global.Promise;
mongoose.connect(config.mongodb,
        { user: config.mongouser,
          pass: config.mongopass,
          useMongoClient: true });

// set up body parser
app.use(bodyParser.urlencoded({ extended: true }));
app.use(bodyParser.json());

var port = process.env.PORT || config.port;

// routes
var routes = require('./app/routes/routes');
routes(app);

// listen
app.listen(port);
console.log('listening on port: ' + port);
console.log(config.mongodb);
