import os
import json
from lxml import etree
import re
import glob
import chardet


files = glob.glob('tests/docs/response_*.json')

pttn = u'^<!\[CDATA\[(.*?)\]\]>$'

parser = etree.XMLParser(encoding="utf-8")

'''
if they are all ascii how is the one in japanese?
'''

for f in files:
	with open(f, 'r') as g:
		data = json.loads(g.read())

	raw_content = data['raw_content'].encode('unicode_escape')
	m = re.search(pttn, raw_content)
	raw_content = m.group(1)
	try:
		raw_content = raw_content.decode('string_escape').strip().decode('unicode_escape').encode('utf-8')
	except Exception as ex:
		with open('nutch_errors.csv', 'a') as g:
			g.write('|'.join([data['digest'], data['id'], ex.message.encode('unicode_escape').encode('utf-8', 'ignore')]) + '\n')
		continue

	try:
		xml = etree.fromstring(raw_content, parser)
	except Exception as ex:
		with open('nutch_errors.csv', 'a') as g:
			g.write('|'.join([data['digest'], data['id'], ex.message.encode('unicode_escape').encode('utf-8', 'ignore')]) + '\n')
		continue

	#pull the namespaces
	namespaces = dict(xml.xpath('/*/namespace::*'))

	repacked = []
	for p, n in namespaces.iteritems():
		repacked.append(','.join([data['digest'], data['id'], (p if p else 'default'), n]))

	with open('nutch_namespaces.csv', 'a') as g:
		g.write('\n'.join(repacked) + '\n')


