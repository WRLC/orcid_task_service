import requests
import json
import lxml
import re
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

WORK_REL = {
    "uri":"info:fedora/fedora-system:def/model#",
    "predicate":"hasModel",
    "object":"ir:citationCModel",
    "type":"uri"
}

API_ENDPOINT = 'https://auislandora-dev.wrlc.org/islandora/rest/v1/'

ORCID_WORK_ENDPOINT = 'https://pub.orcid.org/v2.0/{}/work/{}'

ORCID_REGEX = re.compile('[0-9]{4}-[0-9]{4}-[0-9]{4}-[0-9]{4}')

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
    r_dict['title'] = extract_attr(req_json['authority']['titleInfo'], 'title')
    r_dict['organization'] = extract_attr(req_json['affiliation'], 'organization')
    r_dict['url'] = extract_attr(req_json, 'url')
    if 'note' in req_json:
        if 'history' in req_json['note']:
            r_dict['history'] = extract_attr(req_json['note'], 'history')
    else:
        r_dict['history'] = False
    r_dict['position'] = extract_attr(req_json['affiliation'], 'position')
    if 'citations' in req_json:
        r_dict['citations'] = extract_attr(req_json, 'citations')

    return(r_dict)

def get_researcher(session, researcher_dict):
    '''
    Check if researcher exists in islandora. Match on email.
    '''
    result = {
        "pid" : False,
        "id_type" : None
    }
    res = session.get(API_ENDPOINT + 'solr/MADS_u1_ms:' + researcher_dict['email'])
    response_data = json.loads(res.content.decode('utf-8'))
    if response_data['response']['numFound'] == 1:
        result['pid'] = response_data['response']['docs'][0]['PID']
        result['id_type'] = "email"
        return(result)
    elif response_data['response']['numFound'] == 0:
        # if email isn't found, check if orcid is already there
        orcid_search_request = session.get(API_ENDPOINT + 'solr/MADS_u1_ms:*' + researcher_dict['orcid'])
        orcid_search_data = json.loads(orcid_search_request.content.decode('utf-8'))
        if orcid_search_data['response']['numFound'] == 1:
            result['pid'] = orcid_search_data['response']['docs'][0]['PID']
            result['id_type'] = "orcid"
            return(result)
        else:
            return(result)
    else:
        failure()

def create_object(session, response_dict, label):
    '''
    Create researcher new object.
    '''
    payload = {
                "namespace" :"auislandora",
                "label" : label,
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
    mads_tree = lxml.etree.parse('app/utils/templates/mads_template.xml')
    mads_tree.find('.//{http://www.loc.gov/mads/v2}email').text = researcher_dict['email']
    
    # must have orcid, names, email
    mads_tree.find(".//{http://www.loc.gov/mads/v2}namePart[@type='given']").text = researcher_dict['given_name']
    mads_tree.find(".//{http://www.loc.gov/mads/v2}namePart[@type='family']").text = researcher_dict['family_name']
    mads_tree.find(".//{http://www.loc.gov/mads/v2}identifier[@type='u1']").text = researcher_dict['orcid']

    # optional values 
    if researcher_dict['url']:
        mads_tree.find('{http://www.loc.gov/mads/v2}url').text = researcher_dict['url'][0]
    if researcher_dict['history']:
        mads_tree.find("{http://www.loc.gov/mads/v2}note[@type='history']").text = researcher_dict['history']
    if researcher_dict['title']:
        mads_tree.find('{http://www.loc.gov/mads/v2}title').text = researcher_dict['title']
    if researcher_dict['organization']:
        mads_tree.find('{http://www.loc.gov/mads/v2}organization').text = researcher_dict['organization']
    if researcher_dict['position']:
        mads_tree.find('{http://www.loc.gov/mads/v2}position').text = researcher_dict['position']
    
    # set up payload and post

    data = {
        'dsid': 'MADS',
        'controlGroup': 'M',
    }
    files = {'mads.xml': lxml.etree.tostrin(mads_tree)}
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
    mads_tree = lxml.etree.fromstring(get_res.content)

    # store the orginal identifer
    original_u1 = mads_tree.find(".//{http://www.loc.gov/mads/v2}identifier[@type='u1']").text
    # store the new identifier
    new_u1 = 'http://orcid.org/' + researcher_dict['orcid']

    # update orcid
    mads_tree.find(".//{http://www.loc.gov/mads/v2}identifier[@type='u1']").text = new_u1
    files = {'mads.xml': lxml.etree.tostring(mads_tree)}
    data = {
        'dsid': 'MADS',
        'controlGroup': 'M',
    }

    ## delete existing mads
    delete_res = session.delete(API_ENDPOINT + 'object/{}/datastream/MADS'.format(pid))

    # post new mads
    post_res = session.post(API_ENDPOINT + 'object/{}/datastream'.format(pid), data=data, files=files)

    # if there are existing citatoins update the linking field
    # on those citations at the same time as we update the profile
    mods_update_results = update_mods(session, original_u1, new_u1)

    record_response(response_dict, post_res)
    return(post_res.status_code)

def create_mods(response_dict, researcher_dict):
    '''
    Create MODS datastream for work from ORCID.
    '''
    # set up xsl
    xsl = lxml.etree.parse('app/utils/templates/orcid_to_mods.xsl')
    transform = lxml.etree.XSLT(xsl)

    # get citiations from orcid
    citation_ids = researcher_dict['citations'].split('/')[-1].split(',')
    
    # colllect work title and mods
    works = []

    for id in citation_ids:
        r = requests.get(ORCID_WORK_ENDPOINT.format(researcher_dict['orcid'], id))
        orcid_xml = lxml.etree.fromstring(r.content)
        work = {}
        try:
            mods_xml = transform(orcid_xml)
            work['title'] = mods_xml.find('.//{http://www.loc.gov/mods/v3}title').text
            work['mods'] = lxml.etree.tostring(mods_xml, pretty_print=True)
            works.append(work)
        except:
            work['title'] = False
            work['mods'] = False
            work['orcid_url'] = r.url
            works.append(work)

    return(works)

def update_mods(session, original_id, new_id):
    '''
    Update MODS datastream dislplayForm field. returns a list
    of updated records.
    '''
    # clean input, islandora api can't handle scheme in search
    # we'll assume an email has an @
    if '@' in original_id:
        query = original_id
    elif 'orcid' in original_id:
        query = '*' + ORCID_REGEX.search(original_id).group()

    search_response = session.get(API_ENDPOINT + 'solr/mods_name_personal_author_displayForm_ms:' + query)
    search_results = search_response.json()

    # get pids, and update associated mods
    mods_pids = []
    for doc in search_results['response']['docs']:
        mods_pid = doc['PID']
        mods_get_res = session.get(API_ENDPOINT + 'object/{}/datastream/MODS'.format(mods_pid))
        mods_soup = BeautifulSoup(mods_get_res.content, "xml")
        mods_soup.find('displayForm').string = new_id
        
        # set up post request
        files = {'mods.xml': mods_soup.prettify()}
        data = {
            'dsid': 'MODS',
            'controlGroup': 'M',
        }

        # delete the existing mods
        mods_delete_res = session.delete(API_ENDPOINT + 'object/{}/datastream/MODS'.format(mods_pid))

        # post new mads
        mods_post_res = session.post(API_ENDPOINT + 'object/{}/datastream'.format(mods_pid), data=data, files=files)

        if mods_post_res.status_code == 201:
            mods_pids.append('updated: ' + mods_pid)
        else:
            mods_pids.append('failed to update: ' + mods_pid)

    return(mods_pids)

def post_mods(session, response_dict, pid, mods):
    response_dict['post_result'] = []
    # set up payload and post
    data = {
        'dsid': 'MODS',
        'controlGroup': 'M',
    }
    files = {'mods.xml': mods}
    res = session.post(API_ENDPOINT + 'object/{}/datastream'.format(pid), data=data, files=files)
    response_dict['post_result'].append(res.status_code)

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

def main():
    r = {'calls' : [],
        'computed_status' : 500,
        'result' : None
    }
    researcher_attrs = build_researcher_dict()
    s = requests.session()
    islandora_auth(s)
    # look up reseracher by email
    researcher_search = get_researcher(s, researcher_attrs)
    pid = researcher_search['pid']
    # if the researcher does not exist, build from scratch
    if pid == False:
        researcher_label = researcher_attrs['given_name'] + ' ' + researcher_attrs['family_name']
        pid = create_object(s, r, researcher_label)
        build_rel(s, r, pid, PERSON_REL)
        build_rel(s, r, pid, MEMBER_OF_REL)
        create_mads(s, r, pid, researcher_attrs)
        add_tn(s, r, pid)
        describe_mads(s, r, pid)
        
        # since this is a new account, we'll grab all citation
        # from the orcid API

        # collect information from orcid api and build mods files
        works_list = create_mods(r, researcher_attrs)
        
        # We'll send pids created in the response
        r['citations_created'] = []

        #create object, rels-ext, mods for each citation
        for work in works_list:
            work_pid = create_object(s, r, work['title'])
            build_rel(s, r, work_pid, WORK_REL) 
            if work['mods']:
                post_mods(s, r, work_pid, work['mods'])
                r['citations_created'].append(work_pid)
            else:
                r['citations_created'].append('failed to parse {}'
                    .format(work['orcid_url']))

   # if the reseracher does exists, update the researcher
    elif researcher_search['id_type'] == "email":
        update_mads(s, r, pid, researcher_attrs)
        r['result'] = "updated"
        r['computed_status'] = 201
    else:
        r['result'] = "pass"
        r['computed_status'] = 201
   
    r['resource_uri'] = 'https://auislandora-dev.wrlc.org/islandora/object/' + pid
    for call in r['calls']:
        if list(call.values())[0] > 299:
           break
        else:
           r['computed_status'] = 201
    print(json.dumps(r))

if __name__ == '__main__':
    main()
