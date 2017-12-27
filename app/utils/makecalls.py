import requests
import json
import sys
from api_settings import *
from bs4 import BeautifulSoup

# reqeust body (JSON) passed in as command line arg
req_json = json.loads(sys.argv[1])

# RELS-EXTS
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
    '''
    Authenticate to islandora.
    '''
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

def extract_attr(req_dict, key):
    '''
    Get attribute key from request dictorary body.
    '''
    if key in req_dict:
        return(req_dict[key])
    else:
        return(False)

def build_researcher_dict():
    '''
    Build dictionary of possible mads attrs from request body.
    '''
    r_dict = {}
    r_dict['email'] = extract_attr(req_json['identifier'], 'netid')
    r_dict['given_name'] = extract_attr(req_json['authority']['name'], 'given')
    r_dict['family_name'] = extract_attr(req_json['authority']['name'], 'family')
    r_dict['orcid'] = extract_attr(req_json['identifier'], 'u1')
    r_dict['title'] = extract_attr(req_json['affiliation'], 'position')
    r_dict['organization'] = extract_attr(req_json['affiliation'], 'organization')
    r_dict['url'] = extract_attr(req_json, 'url')
    if 'history' in req_json:
        r_dict['history'] = extract_attr(req_json['note'], 'history')
    else:
        r_dict['history'] = False
    r_dict['position'] = extract_attr(req_json['affiliation'], 'position')

    return(r_dict)

def get_researcher(session, email):
    '''
    Check if researcher exists in islandora. Match on email.
    '''
    res = session.get(API_ENDPOINT + 'solr/MADS_email_ms:' + email)
    response_data = json.loads(res.content.decode('utf-8'))
    if response_data['response']['numFound'] == 1:
        return(response_data['response']['docs'][0]['PID'])
    elif response_data['response']['numFound'] == 0:
        return(False)
    else:
        failure()

def create_researcher(session, response_dict, researcher_dict):
    '''
    Create researcher datastream in islandora and return PID.
    '''
    payload = {
                "namespace" :"auislandora",
                "label" : researcher_dict['given_name'] + ' ' + researcher_dict['family_name'],
                "owner" : "admin"
            }
    res = session.post(API_ENDPOINT + 'object', data=payload)
    if res.status_code == 201:
        record_response(response_dict, res)
        return(json.loads(res.content.decode('utf-8'))['pid'])
    else:
        failure()

def build_rel(session, response_dict, pid, payload):
    '''
    Add relationships to define datastream as researcher.
    '''
    res = session.post(API_ENDPOINT + 'object/{}/relationship'.format(pid), data=payload)
    record_response(response_dict, res)
    return({
        'endpoint' : res.url,
        'status_code' : res.status_code
    })

def create_mads(session, response_dict, pid, researcher_dict):
    '''
    Populate MADS with data from request body.
    '''
    
    # modify MADs template
    with open('app/utils/templates/mads_template.xml', 'rb') as fh:
        mads = fh.read()
    mads_soup = BeautifulSoup(mads, "html.parser")
    mads_soup.email.append(researcher_dict['email'])
    
    # must have orcid, names, email
    mads_soup.find(type="given").append(researcher_dict['given_name'])
    mads_soup.find(type="family").append(researcher_dict['family_name'])
    mads_soup.find(type="u1").append('https://orcid.org/' + researcher_dict['orcid'])

    # optional values would be nicer as loop but mads isn't uniform enough
    if researcher_dict['url']:
        mads_soup.find('url').append(researcher_dict['url'][0])
    if researcher_dict['history']:
        mads_soup.find(type="history").append(researcher_dict['history'])
    if researcher_dict['title']:
        mads_soup.find('title').append(researcher_dict['title'])
    if researcher_dict['organization']:
        mads_soup.find('organization').append(researcher_dict['organization'])
    if researcher_dict['position']:
        mads_soup.find('position').append(researcher_dict['position'])
    
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

def update_mads(session, response_dict, pid, researcher_dict):
    '''
    Get existing MADS, modify locally, delte and update.
    Should be replaced with PUT request to modify when updating
    is available in the islandora API.
    '''
    get_res = session.get(API_ENDPOINT + 'object/{}/datastream/MADS'.format(pid))
    mads_soup = BeautifulSoup(get_res.content, "html.parser")
    # update orcid
    mads_soup.find(type="u1").string = 'https://orcid.org/' + researcher_dict['orcid_uri']
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
    '''
    Add default thumbnail image.
    '''
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
    '''
    Set mads type.
    '''
    res = session.get(API_ENDPOINT + '{}/datastream/MADS?content,true'.format(pid))
    record_response(response_dict, res)
    return({
        'endpoint' : res.url,
        'status_code' : res.status_code
    })

def record_response(response_dict, res):
    '''
    record response to Islandora API call.
    '''
    response_dict['calls'].append({res.url : res.status_code})

def failure():
    '''
    return failure information.
    '''
    print('{"status_code" : 500, "message" : "islandora api calls failed"}')
    sys.exit(1)


# def main():
#     # for testing
#     message = {}
#     message['computed_status'] = 200
#     message['testing'] = build_researcher_dict()
#     print(json.dumps(message))

def main():
   r = {'calls' : [],
       'computed_status' : 500,
   }
   researcher_attrs = build_researcher_dict()
   s = requests.session()
   islandora_auth(s)
   # look up reseracher by email
   pid = get_researcher(s, researcher_attrs['email'])
   # if the researcher does not exist, build from scratch
   if pid == False:
       pid = create_researcher(s, r, researcher_attrs)
       build_rel(s, r, pid, PERSON_REL)
       build_rel(s, r, pid, MEMBER_OF_REL)
       create_mads(s, r, pid, researcher_attrs)
       add_tn(s, r, pid)
       describe_mads(s, r, pid)
   # if the reseracher does exist, update the researcher
   else:
       update_mads(s, r, pid, researcher_attrs)
   
   r['resource_uri'] = 'https://auislandora-dev.wrlc.org/islandora/object/' + pid
   for call in r['calls']:
       if list(call.values())[0] > 299:
           break
       else:
           r['computed_status'] = 201
   print(json.dumps(r))

if __name__ == '__main__':
    main()
