// app/routes/routes.js
module.exports = function(app) {
    var apiControllers = require('../controllers/controllers');

    var express = require('express');
    var router = express.Router();

    // middleware TODO, more meaningful logging
    // and error handling
    router.use(function(req, res, next) {
        console.log(req.method + ' ' + req.url);
        next();
    });
    
    router.route('/')
    	.get(apiControllers.doc_message);

    router.route('/researchers')
    	.get(apiControllers.get_researchers)
        .post(apiControllers.create_researcher);

    router.route('/researchers/:orcid')
        .get(apiControllers.get_researcher);

    app.use('/api', router);

};

