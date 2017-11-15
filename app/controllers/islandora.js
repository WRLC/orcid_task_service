// app/controllers/islandora.js
var mongoose = require('mongoose'),
    config = require('../../config'),
    Researcher = mongoose.model('Researcher'),
    request = require('request');

// utility

function islandora_auth() {
	request.post({url: config.islandora.host + '/user/login',
		form: {
			'form_id': 'user_login',
			'name': config.islandora.user,
			'op': 'Log in',
			'pass': config.islandora.password
		}
	},
		function(err, res, body) {
		if(err)
			console.log(err);
	});
}

// controllers

exports.test_islandora = function(req, res) {
	islandora_auth();

	request.get(config.islandora.host + config.islandora.testitem, function(island_err, island_res, island_body) {
		if (island_err)
			res.status(400).send(island_err);
		res.send(island_body);
	});
};

exports.update_islandora = function(req, res) {
	islandora_auth();
    
    request.get(config.islandora.host +
    	'/islandora/rest/v1/solr/MADS_email_ms:' +
    	req.body.identifier.netid,
    	function(island_err, island_res, island_body) {
    		if (island_err)
    			return res.status(400).json({message: 'Researcher lookup failed.'});
    		if (JSON.parse(island_body).response.numFound == 1) {
    			res.json({message: 'update researcher in islandora'});
    		} else if (JSON.parse(island_body).response.numFound == 0){
    			res.json({message: 'create researcher in islandora'});
    		} else {
    			return res.status(500).json({message: 'Internal Error, could not parse islandora response.'})
    		}

    	});

};