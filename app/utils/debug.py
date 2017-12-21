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

print(email + '\n' + given_name + '\n' + family_name + '\n' + orcid)