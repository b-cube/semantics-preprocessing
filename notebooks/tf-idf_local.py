from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics.pairwise import linear_kernel
from sklearn import metrics
import glob
import os

bags = []
files = glob.glob('../testdata/solr_20150320/bow_no_xml/*.txt')
for f in files:
    if '_similarities' in f:
        continue
    i = f.split('/')[-1].replace('.txt', '')
    with open(f, 'r') as g:
        bow = g.read()
    
    bags.append([i, bow])

import time

start_time = time.time()

ptimes = []

# do the tokenization of all the bags first 
# this is not a quick little thing
all_identifiers = [b[0] for b in bags]
all_bags = [b[1] for b in bags]

tfidf_vectorizer = TfidfVectorizer()

for i, bag in enumerate(bags):
    if os.path.exists('../testdata/solr_20150320/bow_no_xml/%s_similarities.txt' % bag[0]):
        continue
    tf_start = time.time()
    tf_identifiers = [all_identifiers[i]] + all_identifiers[:i-1] + all_identifiers[i:]
    tf_data = [all_bags[i]] + all_bags[:i-1] + all_bags[i:]
    
    tfidf_matrix_trainer = tfidf_vectorizer.fit_transform(tf_data)
    
    cos_sim = cosine_similarity(tfidf_matrix_trainer[0:1], tfidf_matrix_trainer)
    
    lk = linear_kernel(tfidf_matrix_trainer[0:1], tfidf_matrix_trainer).flatten()

    related_indices = cos_sim.argsort()[:-len(tf_data)-1:-1] 
    related_indices_with_lk_value = [r for r in related_indices[0] if lk[r] >= 0.1]
    related_indices_with_lk_value.reverse()

    related_set = [(lk[k], tf_data[k], tf_identifiers[k]) for k in related_indices_with_lk_value]
    lines = []
    for cs, b, d in related_set[1:]:
        #print cs, b, d
        lines.append('%s,%s' % (cs, d))
    
    ptimes.append(time.time() - tf_start)
    if i % 50 == 0:
        print time.time() - tf_start
    
    with open('../testdata/solr_20150320/bow_no_xml/%s_similarities.txt' % bag[0], 'w') as g:
        g.write('\n'.join(lines))

print time.time() - start_time

print 'average time:', sum(ptimes) / len(ptimes)
print 'longest running:', max(ptimes)
