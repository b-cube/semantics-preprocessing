import json
import glob

files = glob.glob('testdata/solr_20150320/solr_*.json')

for f in files:
    with open(f, 'r') as g:
        data = json.loads(g.read())

    for doc in data['response']['docs']:
        digest = doc['digest']
        with open('testdata/solr_20150320/docs/%s.json' % digest, 'w') as g:
            g.write(json.dumps(doc, indent=4))
