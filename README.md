# WRLC ORCID task API

This is a demonstartion app to integrate ORCID information with library services. There are two main components:
1. A store of researcher ORCID information exposed via an HTTP API.
2. Optional integrations to send ORCID data to other apps and services. An islandora integration is implemented in this demo. 

## Setup

These setup instructions have been tested on Ubuntu 14.04 and 16.04. The instructions for installing Node and Mongo can be skipped if you prefer to install them a different way.

### Requirements
- [Nodejs](https://nodejs.org)
- [Mongodb](https://www.mongodb.com)

### Islandora integration requirements
- Python3

### Installing

#### Install Nodejs
Tested using nodejs 8.x, Installing from the nodesource PPA.
```bash
wget https://deb.nodesource.com/setup_8.x -O addnodeppa.sh
sudo bash addnodeppa.sh
sudo apt-get install nodejs
nodejs -v
```
The output of nodejs -v should be something like `v8.10.0`.

#### Install MongoDB
Tested using MongoDB 3.6. Installing from the mongodb ppa according to (these instructions)[https://docs.mongodb.com/manual/tutorial/install-mongodb-on-ubuntu/]
```bash
# add gpg key
sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 2930ADAE8CAF5059EE73BB4B58712A2291FA4AD5    

# note that this is sensitive to you distro, use xenial instead of trusty for Ubuntu 16.04
echo "deb [ arch=amd64 ] https://repo.mongodb.org/apt/ubuntu trusty/mongodb-org/3.6 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-3.6.list 

sudo apt-get update

sudo apt-get install mongodb-org
mongo --version
```
The output of `mongo --version` should be something like `MongoDB shell version v3.6.3...`

#### Secure MongoDB
Create a user to administrer accounts
```bash
use admin

db.createUser(
  {
    user: "adminusername",
    pwd: "ADMINPASS",
    roles: [ { role: "userAdminAnyDatabase", db: "admin" } ]
  }
)
```

Create a database and user for orcid_task_service
```bash
use orcid

db.createUser(
  {
    user: "orciduser",
    pwd: "SOMEPASSWORD",
    roles: [ { role: "readWrite", db: "orcid" }]
  }
)
```

Also, be sure that you're mongoDB instance is only listening for connections from places you expect to connect from. On recent versions, the default bind address is 127.0.0.1 which is good if you're hosting mongo on the same machine as orcid_task_service. On some older versions of mongoDB the default bind address is `0.0.0.0`, which you probably do not want.

#### Install orcid_task_service
```bash
git clone https://github.com/WRLC/orcid_task_service.git
```

Install node depenancies
```bash
cd orcid_task_service
npm install
```

### Configuration
Copy config.template.js to config.js and adjust the settings to match your environment:
```bash
cp config.template.js config.js
vi config.js
```
Configure the islandora parameters if you would like to use the islandora integration.

Test by running `nodejs server.js`. If this looks good, It's advisable to use a process manager like pm2 to run your service.

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

## Updating packages

When npm packages require updating, there are two steps to deploying this updates. First, update and install them locally using npm and commit to Git. Then pull updates into production and install them.

### Update package.json locally

1. run `npx npm-check-updates -u` to update package versions in package.json and package-lock.json
1. run `npm install` to install the updates
1. commit updates to Git repo and push to Github

### Install updates in production

Because the `node_modules` directory is not committed to the Git repo, updates must be installed in production after pulling in the updated package versions from Github.

1. run `sudo git pull` to pull in the package.json and package-lock.json updates
1. run `npm install` to install the updated packages
1. run `sudo systemctl restart orcid` to restart orcid_task_service
