import requests
import json
import sys
from api_settings import *
from bs4 import BeautifulSoup

email = sys.argv[1]
given_name = sys.argv[2]
family_name = sys.argv[3]
orcid = sys.argv[4]
orcid_uri = "https://orcid.org/" + orcid

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

API_ENDPOINT = 'https://auislandora-dev.wrlc.org/islandora/rest/v1/'

def islandora_auth(session):
    payload = {
        'form_id': 'user_login',
        'name': islandora_user,
        'op': 'Log in',
        'pass': islandora_password
    }
    loginurl = 'https://auislandora-dev.wrlc.org/user/login'
    login = session.post(loginurl, data=payload)
    if login.status_code == 200:
        return(True)
    else:
        failure()

def get_researcher(session, email):
    res = session.get(API_ENDPOINT + 'solr/MADS_email_ms:' + email)
    response_data = json.loads(res.content.decode('utf-8'))
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
        return(json.loads(res.content.decode('utf-8'))['pid'])
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
    # modify MADs template
    with open('app/utils/templates/mads_template.xml', 'rb') as fh:
        mads = fh.read()
    mads_soup = BeautifulSoup(mads, "html.parser")
    mads_soup.email.append(email)
    mads_soup.find(type="given").append(given_name)
    mads_soup.find(type="family").append(family_name)
    mads_soup.find(type="u1").append(orcid_uri)
    # set up payload and post
    data = {
        'dsid': 'MADS',
        'controlGroup': 'M',
    }
    files = {'mads.xml': mads_soup.prettify()}
    res = session.post(API_ENDPOINT + 'object/{}/datastream'.format(pid), data=data, files=files)
    record_response(response_dict, res)
    return({
        'endpoint' : res.url,
        'status_code' : res.status_code
    })

def update_mads(session, response_dict, pid):
    get_res = session.get(API_ENDPOINT + 'object/{}/datastream/MADS'.format(pid))
    mads_soup = BeautifulSoup(get_res.content, "html.parser")
    # update orcid
    mads_soup.find(type="u1").string = orcid_uri
    files = {'mads.xml': mads_soup.prettify()}
    data = {
        'dsid': 'MADS',
        'controlGroup': 'M',
    }

    ## delete existing mads
    delete_res = session.delete(API_ENDPOINT + 'object/{}/datastream/MADS'.format(pid))

    # post new mads
    post_res = session.post(API_ENDPOINT + 'object/{}/datastream'.format(pid), data=data, files=files)
    record_response(response_dict, post_res)
    return(post_res.status_code)

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
    print('{"status_code" : 500, "message" : "islandora api calls failed"}')
    sys.exit(1)

def main():
    r = {'calls' : [],
        'computed_status' : 500,
    }
    s = requests.session()
    islandora_auth(s)
    # look up reseracher by email
    pid = get_researcher(s, email)
    r['resource_uri'] = API_ENDPOINT + '/islandora/object/' + pid
    # if the researcher does not exist, build from scratch
    if pid == False:
        pid = create_researcher(s, r)
        build_rel(s, r, pid, PERSON_REL)
        build_rel(s, r, pid, MEMBER_OF_REL)
        create_mads(s, r, pid)
        add_tn(s, r, pid)
        describe_mads(s, r, pid)
    # if the reseracher does exist, update the researcher
    else:
        update_mads(s, r, pid)

    for call in r['calls']:
        if list(call.values())[0] > 299:
            break
        else:
            r['computed_status'] = 200
    print(json.dumps(r))

if __name__ == '__main__':
    main()
