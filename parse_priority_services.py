import glob
import json
from lib.identifier import Identify
from lib.parser import Parser
from lib.rawresponse import RawResponse
from lib.preprocessors.opensearch_preprocessors import OpenSearchReader
from lib.preprocessors.iso_preprocessors import IsoReader
from lib.preprocessors.oaipmh_preprocessors import OaiPmhReader
from lib.preprocessors.thredds_preprocessors import ThreddsReader

import logging

'''
and now let's parse some xml

starting with the high priority responses

we're going to
1. identify a response
2. if it's high priority, parse into the new json
3. save it to disk
'''

logging.basicConfig(level=logging.WARN)
logger = logging.getLogger(__name__)

YAML_FILE = 'lib/configs/identifiers.yaml'

responses = glob.glob('testdata/docs/response_*.json')

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

    identifier = Identify(YAML_FILE, cleaned_text, url, **{'parser': parser, 'ignore_case': True})
    try:
        identifier.identify()
    except Exception as ex:
        continue

    protocol = identifier.protocol
    service = identifier.service
    has_dataset = identifier.has_dataset
    has_metadata = identifier.has_metadata
    version = identifier.version
    is_error = identifier.is_error
    subtype = identifier.subtype

    print digest, protocol, service, version
    if not identifier.protocol or is_error:
        continue

    # now let's get a preprocessor
    # which creates its own parser
    if protocol == 'OpenSearch':
        reader = OpenSearchReader(cleaned_text)
    elif protocol == 'UNIDATA':
        reader = ThreddsReader(cleaned_text)
    elif protocol == 'ISO-19115':
        reader = IsoReader(cleaned_text)
    elif protocol == 'OAI-PMH':
        reader = OaiPmhReader(cleaned_text)
    elif 'OGC' in protocol and protocol != 'OGC:error':
        continue

    service_description = reader.parse_service()
    service_description['solr_identifier'] = digest
    service_description['source_url'] = url
    service_description['harvested_date'] = data['date'] if 'date' in data else ''

    # and add the identification information
    service_description['identity'] = identifier.to_json()

    # this should be everything needed to generate the triples
    with open('testdata/service_descriptions/%s.json' % digest, 'w') as f:
        f.write(json.dumps(service_description, indent=4))

    identifier = None
