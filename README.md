# WRLC ORCID task API

This is a demonstartion app to integrate ORCID information with library services. There are two main components:
1. A store of researcher ORCID information exposed via an HTTP API.
2. Optional integrations to send ORCID data to other apps and services. An islandora integration is implemented in this demo. 

## Installing

### Requirements
- Nodejs
- Mongodb
- Python3 (for islandora integration)

### Configuration
Copy config.template.js to config.js and adjust the settings to match your environment:
```
cp config.template.js config.js
vi config.js
```

### Researcher ORCID API

#### Get Researcher by ORCID

GET `http://HOSTNAME:PORT/api/researchers/:orcid`

example: `http://HOSTNAME:PORT/api/researchers/12345-12345-12345`

#### Get all Researchers
GET `http://HOSTNAME:PORT/api/researchers`

#### Create or Update Researcher
PUT `http://HOSTNAME:PORT/api/researchers/:orcid`

Body should be researcher as JSON. 

Example Request:
PUT `http://HOSTNAME:PORT/api/researchers/12345-12345-1234`
Example Body:
```json
{
    "orcid": "54321-54321-54321",
    "access_token": "token",
    "token_type": "bearer",
    "refresh_token": "another token",
    "expires_in": 3599,
    "scope": "default: read-limited activties update",
    "name": "sarah sarahsen"
}
```
#### Delete Researcher
DELETE `http://HOSTNAME:PORT/api/researchers/:orcid`

Example Request:
DELETE `http://HOSTNAME:PORT/api/researchers/1234-1234-1234`

### Islandora Integration API

#### Create or update researcher and citations
This call will attempt to create a researcher profile in Islandora. It will attempt to pull in any citations available in ORCID as well. Researcher and citaiton information is passed in the request body.
PUT `http:HOSTNAME:PORT/api/islandora/:orcid`

Example Request:
PUT `http:HOSTNAME:PORT/api/islandora/1234-1234-1234-1234`

Example Body:
```json
{
  "identifier": {
    "u1": "1234-1234-1234-1234",
    "netid": "email@institution.edu"
  },
  "authority": {
    "name": {
      "given": "GIVEN_NAME",
      "family": "SURNAME"
    },
    "titleInfo": {
      "title": "TITLE"
    }
  },
  "affiliation": {
    "organization": "ORGANIZATION NAME",
    "position": "POSITION"
  },
  "url": [
    "https://www.website.tld/"
  ],
  "note": {
    "history": "Biography paragraph."
  },
  "citations": "https://pub.orcid.org/v2.0/1234-1234-1234-1234/works/1234567,89101112,13141516"
}
```
Note that `u1` is the ORCID, and `netid` is an unique id (in this case email).
Example Body:
