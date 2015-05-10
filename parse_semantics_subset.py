import os
import glob
import json

from lib.rawresponse import RawResponse
from lib.process_router import Processor

types = ['iso', 'oaipmh', 'opensearch', 'ogc']
files = []
for t in types:
    files += glob.glob('../semantics/service_examples/%s/identification_results/*.json' % t)


for f in files:
    print f
    with open(f, 'r') as g:
        data = json.loads(g.read())
    identity = data.get('identity', {})
    protocol = identity.get('protocol', '')
    source_url = data['url']

    if not protocol:
        continue

    content = data['raw_content']

    rr = RawResponse(source_url.upper(), content, data['digest'], **{})
    content = rr.clean_raw_content()
    content = content.encode('unicode_escape')

    processor = Processor(identity, content, source_url)
    if not protocol:
        continue

    print identity

    service = processor.reader.parse_service()

    data.update({"service_description": service})
    del data['raw_content']
    del data['content']

    outdir = '/'.join(f.split('/')[:-2])

    with open(os.path.join(outdir, os.path.basename(f)), 'w') as g:
        g.write(json.dumps(data, indent=4))
