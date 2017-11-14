// app/routes/routes.js
module.exports = function(app) {
    var apiControllers = require('../controllers/controllers');
    var islandoraControllers = require('../controllers/islandora');

    var express = require('express');
    var router = express.Router();

    // middleware TODO, more meaningful logging
    // and error handling
    router.use(function(req, res, next) {
        console.log(req.method + ' ' + req.url);
        next();
    });
    
    // researchers api

    router.route('/')
    	.get(apiControllers.doc_message);

    router.route('/researchers')
    	.get(apiControllers.get_researchers)
        .post(apiControllers.create_researcher);

    router.route('/researchers/:orcid')
        .get(apiControllers.get_researcher)
        .put(apiControllers.update_researcher)
        .post(apiControllers.post_error)
        .delete(apiControllers.delete_researcher);

    // islandora tasks

    router.route('/islandora/test')
    	.get(islandoraControllers.test_islandora);

    app.use('/api', router);

};

