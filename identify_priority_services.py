import glob
import json
from lib.identifier import Identify
from lib.parser import Parser
from lib.rawresponse import RawResponse
import logging

'''
so a quick script to demonstrate the identification
process against a local file store of solr responses
'''

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

YAML_FILE = 'lib/configs/all_identifiers.yaml'

# responses = glob.glob('testdata/docs/response_60de9ec6341a2116ff4bb2739c307739.json')
responses = glob.glob('testdata/docs/response_*.json')

# with open('testdata/probable_ogc.txt', 'r') as f:
#     digests = f.readlines()
# responses = ['testdata/docs/response_%s.json' % d.strip() for d in digests]

with open('priority_identification_all.csv', 'w') as f:
    f.write('digest|url|protocol|subtype|service|has dataset|has metadata|version|is error\n')

for response in responses:
    with open(response, 'r') as f:
        data = json.loads(f.read())

    digest = data['digest']
    raw_content = data['raw_content']
    url = data['url']

    rr = RawResponse(url.upper(), raw_content, digest, **{})
    cleaned_text = rr.clean_raw_content()
    cleaned_text = cleaned_text.strip()

    try:
        parser = Parser(cleaned_text)
    except Exception as ex:
        logger.debug('xml parsing error: %s' % digest, exc_info=1)
        continue

    print digest

    identifier = Identify(YAML_FILE, cleaned_text, url, **{'parser': parser, 'ignore_case': True})
    identifier.identify()
    protocol = identifier.protocol
    subtype = identifier.subtype
    service = identifier.service
    has_dataset = identifier.has_dataset
    has_metadata = identifier.has_metadata
    version = identifier.version
    is_error = identifier.is_error

    # if not protocol:
    #     continue

    with open('priority_identification_all.csv', 'a') as f:
        f.write('|'.join([digest, url.replace(',', ';').replace('|', ';'), protocol, subtype, service,
                str(has_dataset), str(has_metadata), str(version), str(is_error)]) + '\n')
