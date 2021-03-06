// app/controllers/islandora.js
var mongoose = require('mongoose'),
	config = require('../../config'),
	Researcher = mongoose.model('Researcher'),
	request = require('request-promise').defaults({ simple: false }),
	spawn = require('child_process').spawn,
	//request = require('request'),
	async = require('async');

// utility

function islandora_auth() {
	request.post({url: config.islandora.host + '/user/login',
		form: {
			'form_id': 'user_login',
			'name': config.islandora.user,
			'op': 'Log in',
			'pass': config.islandora.password
		},
		jar : true
	},
		function(err, res, body) {
		if(err)
			console.log(err);
		console.log(res.body);
	});
}

// controllers
exports.islandora_create_or_update = function(req, res) {
	var py = spawn('python3', ['app/utils/makecalls.py',
		JSON.stringify(req.body)]);
	py.stdout.on('data', function(data) {
		res.status(JSON.parse(data).computed_status).send(data);
	});
	py.stderr.on('data', function(data) {
		res.status(500).send(data)
	});


};

exports.test_islandora = function(req, res) {
	var py = spawn('python3', ['app/utils/debug.py',
		req.body.identifier.netid,
		req.body.authority.name.given,
		req.body.authority.name.family,
		req.body.identifier.u1]);
	py.stdout.on('data', function(data){
		res.send(data)
	})


};