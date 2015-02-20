import glob
import json
from lib.identifier import Identify
from lib.parser import Parser
from lib.rawresponse import RawResponse
import traceback
import sys

'''
so a quick script to demonstrate the identification
process against a local file store of solr responses
'''

YAML_FILE = 'lib/configs/identifiers.yaml'

# responses = glob.glob('testdata/docs/response_60de9ec6341a2116ff4bb2739c307739.json')
# responses = glob.glob('testdata/docs/response_*.json')

with open('testdata/probable_ogc.txt', 'r') as f:
    digests = f.readlines()
responses = ['testdata/docs/response_%s.json' % d.strip() for d in digests]

with open('priority_identification_ogc.csv', 'w') as f:
    f.write('digest|url|protocol|service|is dataset|version|is error\n')

for response in responses[0:5]:
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
        print 'xml parsing error: ', ex, digest
        traceback.print_exc(file=sys.stdout)
        continue

    identifier = Identify(YAML_FILE, cleaned_text, url, **{'parser': parser, 'ignore_case': True})
    protocol, service, is_dataset, version, is_error = identifier.identify()

    print digest, protocol, service, version, is_error

    with open('priority_identification_ogc.csv', 'a') as f:
        f.write('|'.join([digest, url.replace(',', ';').replace('|', ';'), protocol, service,
                str(is_dataset), version, str(is_error)]) + '\n')
