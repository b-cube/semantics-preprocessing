import json
import glob

files = glob.glob('testdata/second_harvest/response_*.json')

for f in files:
    with open(f, 'r') as g:
        data = json.loads(g.read())

    for doc in data['response']['docs']:
        digest = doc['digest']
        with open('testdata/second_harvest/docs/%s.json' % digest, 'w') as g:
            g.write(json.dumps(doc, indent=4))
