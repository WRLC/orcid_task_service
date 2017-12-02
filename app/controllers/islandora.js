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
		console.log(res);
	});
}

// controllers
exports.islandora_create_or_update = function(req, res) {
	var py = spawn('python', ['app/utils/makecalls.py',
		req.body.identifier.netid,
		req.body.authority.name.given,
		req.body.authority.name.family,]);
	py.stdout.on('data', function(data){
		res.send(data);
	});


};

exports.test_islandora = function(req, res) {
	islandora_auth();

	request.get({
				url: config.islandora.host + config.islandora.testitem,
				json: true
			},
		function(island_err, island_res, island_body) {
		if (island_err)
			res.status(400).send(island_err);
	}).then(function (response) {
        //console.log(JSON.parse(res).pid);
        console.log(response);
        res.send(response.pid);
    });
};