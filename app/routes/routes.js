// app/routes/routes.js
module.exports = function(app) {
    var apiControllers = require('../controllers/controllers');

    var express = require('express');
    var router = express.Router();
    var config = require('../../config');

    // middleware TODO, more meaningful logging
    // and error handling
    router.use(function(req, res, next) {
        console.log(req.method + ' - ' + req.url + ' - ' + JSON.stringify(req.body));
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
    
    if ( typeof config.islandora !== 'undefined' ) {
        var islandoraControllers = require('../controllers/islandora');

        router.route('/islandora/test')
        	.put(islandoraControllers.test_islandora);

        router.route('/islandora/:orcid')
            .put(islandoraControllers.islandora_create_or_update);

    }

        app.use('/api', router);
};
