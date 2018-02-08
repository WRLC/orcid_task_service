import requests
import json
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
    res = session.get(API_ENDPOINT + 'solr/MADS_email_ms:' + researcher_dict['email'])
    response_data = json.loads(res.content.decode('utf-8'))
    if response_data['response']['numFound'] == 1:
        return(response_data['response']['docs'][0]['PID'])
    elif response_data['response']['numFound'] == 0:
        # if email isn't found, check if orcid is already there
        orcid_search_request = session.get(API_ENDPOINT + 'solr/MADS_u1_ms:*' + researcher_dict['orcid'])
        orcid_search_data = json.loads(orcid_search_request.content.decode('utf-8'))
        if orcid_search_data['response']['numFound'] == 1:
            return(orcid_search_data['response']['docs'][0]['PID'])
        else:
            return(False)
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
    with open('app/utils/templates/mads_template.xml', 'rb') as fh:
        mads = fh.read()
    mads_soup = BeautifulSoup(mads, "html.parser")
    mads_soup.email.append(researcher_dict['email'])
    
    # must have orcid, names, email
    mads_soup.find(type="given").append(researcher_dict['given_name'])
    mads_soup.find(type="family").append(researcher_dict['family_name'])
    mads_soup.find(type="u1").append('http://orcid.org/' + researcher_dict['orcid'])

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

    # store the orginal identifer
    original_u1 = mads_soup.find(type="u1").string
    # store the new identifier
    new_u1 = 'http://orcid.org/' + researcher_dict['orcid']

    # update orcid
    mads_soup.find(type="u1").string = new_u1
    files = {'mads.xml': mads_soup.prettify()}
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

    # make xml soup from orcid response
    orcid_response = requests.get(researcher_dict['citations'])
    orcid_soup = BeautifulSoup(orcid_response.content, "xml")
    orcid_works = orcid_soup.find_all('work:work')

    # list of dictionaries of work attributes
    works = []
    # list of completed Mods

    for work in orcid_works:
        work_dict = {}
        # get put code for work
        work_dict['put_code'] = work.attrs['put-code']
        # get orcid for work
        try:
            work_dict['orcid_uri'] = work.find('uri').text.strip()
        except AttributeError as er:
            print(er)
        # get title for work
        try:
            work_dict['title'] = work.find('title').text.strip()
        except AttributeError:
            work_dict['title'] = None
        # get date for work
        try:
            work_dict['date'] = work.find('publication-date').text.strip()
        except AttributeError:
            work_dict['date'] = None
        # get external url if exists
        try:
            work_dict['external_uri'] = work.find('external-id-url').text.strip()
        except AttributeError:
            work_dict['external_uri'] = None
        # get external url relationship
        try:
            work_dict['external_uri_relationship'] = work.find('external-id-relationship').text.strip()
        except AttributeError:
            work_dict['external_uri_relationship'] = None
        # get citation if exists
        try:
            work_dict['citation'] = work.find('citation-value').text.strip()
        except AttributeError:
            work_dict['citation'] = None

        # get source publication for work
        # should I check for work type, handle differently if it's a 
        # book chapter / monograph / serial / somethign else?

        # add work to list
        works.append(work_dict)

    # open the template do this part for each work found
    for work in works:
        with open('app/utils/templates/mods_template.xml', 'rb') as fh:
            mods = fh.read()
            mods_soup = BeautifulSoup(mods, "xml")
            # orcid (must exist)
            mods_soup.find('displayForm').append(work['orcid_uri'])
            # put code (must exist)
            mods_soup.find('identifier').append(work['put_code'])
            # title
            if work['title']:
                mods_soup.find('title').append(work['title'])
            # author name from researcher dict
            if researcher_dict['given_name']:
                mods_soup.find(type="given").append(researcher_dict['given_name'])
            if researcher_dict['family_name']:
                mods_soup.find(type="family").append(researcher_dict['family_name'])
            # date
            if work['date']:
                mods_soup.find('dateIssued').append(work['date'])
            # external uri
            if work['external_uri']:
                mods_soup.location.url.append(work['external_uri'])
                if work['external_uri_relationship']:
                    mods_soup.location.url['note'] = work['external_uri_relationship']
            # citation
            if work['citation']:
                citation_tag = mods_soup.new_tag("mods:note", type="citation/reference")
                citation_tag.append(work['citation'])
                mods_soup.mods.append(citation_tag)

            # add completed mods to list to be posted
            work['mods'] = (mods_soup.prettify())
            fh.close()

    # return something
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
    }
    researcher_attrs = build_researcher_dict()
    s = requests.session()
    islandora_auth(s)
    # look up reseracher by email
    pid = get_researcher(s, researcher_attrs)
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
            post_mods(s, r, work_pid, work['mods'])
            r['citations_created'].append(work_pid)


   # if the reseracher does exists, update the researcher
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
