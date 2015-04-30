import glob
import json
import urlparse
import time
from simhash import Simhash, SimhashIndex

'''
for simhash testing without taking down chrome/ipy notebook
'''

files = glob.glob('testdata/solr_20150320/identify_20150325_p/*.json')


def parse_url(url):
    parsed = urlparse.urlparse(url)

    base_url = urlparse.urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        None,
        None
    ))

    # return base_url, urlparse.parse_qs(parsed.query)
    return base_url, parsed.query

urls = []
for f in files:
    with open(f, 'r') as g:
        data = json.loads(g.read())

    url = data['source_url']
    identity = data['identity']

    # let's just ignore anything not identified (we got plenty)
    if not identity['protocol']:
        continue

    protocol = identity['protocol']

    urls.append((url, protocol))

# let's generate the simhash singletons
# and generate the index (this cannot be performant)
test_index = [(u[0], Simhash(u[0])) for u in urls]

# simhash_results_a.txt : k=20 (subset)
# simhash_results_b.txt

with open('testdata/solr_20150320/simhash_results_k10.txt', 'w') as f:
    f.write('')

start_time = time.time()

for index, (test_url, test_simhash) in enumerate(test_index):
    i_start_time = time.time()
    if index % 50 == 0:
        print 'completed {0} of {1}'.format(index, len(urls))

    duplicates = []

    for i in xrange(0, len(test_index), 300):
        index = SimhashIndex(test_index[i:i + 300], k=10)
        dupes = index.get_near_dups(test_simhash)

        if len(dupes) > 0:
            duplicates += dupes

    print '\t{0} takes {1}'.format(len(duplicates), time.time() - i_start_time)

    with open('testdata/solr_20150320/simhash_results_k10.txt', 'a') as f:
        f.write(json.dumps({test_url: duplicates}) + '\n')

print 'takes:', time.time() - start_time
