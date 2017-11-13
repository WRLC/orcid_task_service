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
			return res.status(500).send(err);
		if (researcher.length == 0)
			return res.status(404).json({message: 'no researcher found with orcid: ' + req.params.orcid});
		res.json(researcher);
	});
};

exports.get_researchers = function(req, res) {
	Researcher.find({}, function(err, researcher) {
		if (err)
			res.status(400).send(err);
		res.json(researcher);
	});
};

exports.create_researcher = function(req, res) {
	var new_researcher = new Researcher(req.body);
	//new_researcher.orcid = req.body.orcid;

	new_researcher.save(function(err, researcher) {
		if (err) 
			res.status(400).send(err);
		res.json(researcher);
	});
};

exports.update_researcher = function(req, res) {
	Researcher.findOneAndUpdate({orcid: req.params.orcid}, req.body, {new: true}, function(err, researcher) {
		if (err)
			res.status(400).send(err);
		res.json(researcher);
	});
};

exports.delete_researcher = function(req, res) {
	Researcher.remove({orcid: req.params.orcid}, function(err, researcher) {
		if (err)
			res.status(400).send(err);
		res.json({message: 'Deleted reseracher identified by orcid: ' + req.params.orcid})
	});
};
