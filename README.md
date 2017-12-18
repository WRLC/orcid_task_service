# WRLC ORCID task API

Service perform tasks given a researcher's orcid

## Installing

### Requirements
- Nodejs
- Mongodb

### Configuration
Copy config.template.js to config.js and adjust the settings to match your environment:
```
cp config.template.js config.js
vi config.js
```

### Researcher ORCID API

#### Get Researcher by ORCID

GET `http://HOSTNAME:PORT/api/researchers/:orcid`

example: `http://localhost:8181/api/researchers/12345-12345-12345`

#### Get all Researchers
GET `http://HOSTNAME:PORT/api/researchers`

#### Create or Update Researcher
`PUT http://HOSTNAME:PORT/api/researchers/:orcid`

Body should be researcher as JSON. 

Example Request:
`PUT http://localhost:8181/api/researchers/12345-12345-1234`
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
