import os
import glob
import json

from lib.process_router import Processor

files = glob.glob('testdata/solr_20150320/identify_20150325_p/*.json')
outdir = 'testdata/solr_20150320/parsed_20150331'

for f in files:
    with open(f, 'r') as g:
        data = json.loads(g.read())
    identity = data.get('identity', {})
    protocol = identity.get('protocol', '')

    if not protocol:
        continue

    processor = Processor(identity, data['content'], data['source_url'])
    if not protocol:
        continue

    service = processor.parse_service()

    data.update({"service_description": service})
    del data['content']

    with open(os.path.join(outdir, '%s.json' % data['digest']), 'w') as g:
        g.write(json.dumps(data, indent=4))
