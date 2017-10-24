// app/controllers/controllers.js
var mongoose = require('mongoose'),
    config = require('../../config'),
    Researcher = mongoose.model('Researcher');

// controllers
exports.doc_message = function(req, res) {
	res.json({message: config.doc_message});
};

exports.get_researcher = function(req, res) {
	Researcher.find({orcid: req.params.orcid}, function(err, researcher) {
		if (err)
			res.send(err);
		res.json(researcher);
	});
};

exports.get_researchers = function(req, res) {
	Researcher.find({}, function(err, researcher) {
		if (err)
			res.send(err);
		res.json(researcher);
	});
};

exports.create_researcher = function(req, res) {
	var new_researcher = new Researcher(req.body);
	//new_researcher.orcid = req.body.orcid;

	new_researcher.save(function(err, researcher) {
		if (err) 
			res.send(err);
		res.json(researcher);
	});
};