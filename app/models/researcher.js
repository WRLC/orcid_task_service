// app/models/researcher.js

var mongoose = require('mongoose');
var Schema = mongoose.Schema;

var researcherSchema = new Schema({
    orcid: {
        type: String,
	required: true,
	unique: true
    },
    created_date: {
        type: Date,
	default: Date.now
    },
    access_token: {
        type: String,
    },
    token_type: {
        type: String,
        //default: "bearer"
    },
    refresh_token: {
        type: String,
    },
    expires_in: {
        type: Number,
	//default: 3599
    },
    scope: {
        type: String,
        //default: "\/read-limited \/activities \/update"
    },
    name: {
        type: String,
    },
});

module.exports = mongoose.model('Researcher', researcherSchema);
