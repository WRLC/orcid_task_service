// app/controllers/islandora.js
var mongoose = require('mongoose'),
    config = require('../../config'),
    Researcher = mongoose.model('Researcher'),
    request = require('request');

// controllers

exports.test_islandora = function(req, res) {
	var cookieJar = request.jar();
	request.post({url: config.islandora.host + '/user/login',
		jar: cookieJar,
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

	request.get(config.islandora.host + config.islandora.testitem, function(island_err, island_res, island_body) {
		if (island_err)
			res.status(400).send(island_err);
		res.send(island_body);
	});
};

exports.update_islandora = function(req, res) {
	res.json({message: 'update function goes here'});
};