import requests
import json
import sys
from api_settings import *

email = sys.argv[1]
given_name = sys.argv[2]
family_name = sys.argv[3]

PERSON_REL = {
    "uri":"info:fedora/fedora-system:def/model#",
    "predicate":"hasModel",
    "object":"islandora:personCModel",
    "type":"uri"
}

MEMBER_OF_REL = {
    "uri":"info:fedora/fedora-system:def/relations-external#",
    "predicate":"isMemberOfCollection",
    "object":"ir:bios",
    "type":"uri"
}

API_ENDPOINT = 'http://auislandora-dev.wrlc.org/islandora/rest/v1/'

def islandora_auth(session):
    payload = {
        'form_id': 'user_login',
        'name': islandora_user,
        'op': 'Log in',
        'pass': islandora_password
    }
    loginurl = 'http://auislandora-dev.wrlc.org/user/login'
    login = session.post(loginurl, data=payload)
    if login.status_code == 200:
        return(True)
    else:
        failure()

def get_researcher(session, email):
    res = session.get(API_ENDPOINT + 'solr/MADS_email_ms:' + email)
    response_data = json.loads(res.content)
    if response_data['response']['numFound'] == 1:
        return(response_data['response']['docs'][0]['PID'])
    elif response_data['response']['numFound'] == 0:
        return(False)
    else:
        failure()

def create_researcher(session, response_dict):
    payload = {
                "namespace" :"auislandora",
                "label" : given_name + ' ' + family_name,
                "owner" : "admin"
            }
    res = session.post(API_ENDPOINT + 'object', data=payload)
    if res.status_code == 201:
        record_response(response_dict, res)
        return(json.loads(res.content)['pid'])
    else:
        failure()

def build_rel(session, response_dict, pid, payload):
    res = session.post(API_ENDPOINT + 'object/{}/relationship'.format(pid), data=payload)
    record_response(response_dict, res)
    return({
        'endpoint' : res.url,
        'status_code' : res.status_code
    })

def create_mads(session, response_dict, pid):
    data = {
        'dsid': 'MADS',
        'controlGroup': 'M',
    }
    files = {'mads.xml': open('app/utils/templates/mads_template.xml', 'rb')}
    res = session.post(API_ENDPOINT + 'object/{}/datastream'.format(pid), data=data, files=files)
    record_response(response_dict, res)
    return({
        'endpoint' : res.url,
        'status_code' : res.status_code
    })

def add_tn(session, response_dict, pid):
    data = {
        'dsid': 'TN',
        'controlGroup': 'M',
    }
    files = {'mads.xml': open('app/utils/templates/tn.jpg', 'rb')}
    res = session.post(API_ENDPOINT + 'object/{}/datastream'.format(pid), data=data, files=files)
    record_response(response_dict, res)
    return({
        'endpoint' : res.url,
        'status_code' : res.status_code
    })

def describe_mads(session, response_dict, pid):
    res = session.get(API_ENDPOINT + '{}/datastream/MADS?content,true'.format(pid))
    record_response(response_dict, res)
    return({
        'endpoint' : res.url,
        'status_code' : res.status_code
    })

def record_response(response_dict, res):
    response_dict['calls'].append({res.url : res.status_code})

def failure():
    print('{"message" : "islandora api calls failed"}')
    sys.exit(1)

def main():
    r = {'calls' : []}
    s = requests.session()
    islandora_auth(s)
    pid = get_researcher(s, email)
    if pid == False:
        pid = create_researcher(s, r)
    else:
        pass
    build_rel(s, r, pid, PERSON_REL)
    build_rel(s, r, pid, MEMBER_OF_REL)
    create_mads(s, r, pid)
    add_tn(s, r, pid)
    describe_mads(s, r, pid)
    print(r)

if __name__ == '__main__':
    main()
