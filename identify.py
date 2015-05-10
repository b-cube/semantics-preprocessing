import os
import glob
import json

from lib.parser import Parser
from lib.identifier import Identify
from lib.rawresponse import RawResponse

files = glob.glob('testdata/solr_20150320/docs/*.json')
outdir = 'testdata/solr_20150320/identified_20150331'

identifiers = glob.glob('lib/configs/*_identifier.yaml')

for f in files:
    with open(f, 'r') as g:
        data = json.loads(g.read())

    source_url = data['url']
    content = data['raw_content']
    digest = data['digest']

    rr = RawResponse(source_url.upper(), content, digest, **{})
    cleaned_text = rr.clean_raw_content()
    cleaned_text = cleaned_text.encode('unicode_escape')

    parser = Parser(cleaned_text)

    identify = Identify(
        identifiers,
        cleaned_text,
        source_url,
        **{'parser': parser, 'ignore_case': True}
    )
    identify.identify()

    data.update({"identity": identify.to_json()})

    with open(os.path.join(outdir, '%s.json' % digest), 'w') as g:
        g.write(json.dumps(data, indent=4))

    identify = None
