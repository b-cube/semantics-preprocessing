import logging

LOGGER = logging.getLogger(__name__)

def in_url(url, filters):
	'''
	check for some string in a url 
	(not concerned so much about where)
	'''
	url = url.strip()
	return len([f for f in filters if f.strip() in url]) > 0
	

def in_content(content, filters):
	'''
	check for some string in a text blob
	(not concerned so much about where)
	'''    	
	return len([f for f in filters if f in content]) > 0

def identify_protocol(source_content, source_url):
	'''
	basic identification

	note:
		currently starting with high priority service types
	'''
	if in_content(source_content, ['http://www.isotc211.org/2005/gmi', 'http://www.isotc211.org/2005/gmd']):
		#note: not differentiating between versions here
		return 'ISO-19115'
	elif in_content(source_content, ['http://www.unidata.ucar.edu/namespaces/thredds/InvCatalog/v1.0']):
		return 'THREDDS Catalog'
	elif in_content(source_content, ['http://a9.com/-/spec/opensearch/1.1/']):
		return 'OpenSearch'
	elif in_content(source_content, ['http://wadl.dev.java.net']):
		return 'WADL'
	elif in_content(source_content, ['http://www.opengis.net/wms']) or in_url(source_url.upper(), ['SERVICE=WMS']) \
		or (in_content(source_content, ['http://mapserver.gis.umn.edu/mapserver']) and in_url(source_url.upper(), ['SERVICE=WMS'])):
		return 'OGC:WMS'
	elif in_content(source_content, ['http://www.opengis.net/wfs']) or in_url(source_url.upper(), ['SERVICE=WFS']) \
		or (in_content(source_content, ['http://mapserver.gis.umn.edu/mapserver']) and in_url(source_url.upper(), ['SERVICE=WFS'])):
		return 'OGC:WFS'
	elif in_content(source_content, ['http://www.opengis.net/wcs']) or in_url(source_url.upper(), ['SERVICE=WCS']) \
		or (in_content(source_content, ['http://mapserver.gis.umn.edu/mapserver']) and in_url(source_url.upper(), ['SERVICE=WCS'])):
		return 'OGC:WCS'
	elif in_content(source_content, ['http://www.openarchives.org/OAI/']):
		return 'OAI-PMH'

	logger.info('Unable to identify: %s' % source_url)

	return ''

def is_service_description(protocol, source_content, source_url):
	'''
	based on the protocol and source information, identify whether
	a response/service is an acutal service description document or
	some other thing
	'''
	if protocol in ['OGC:WMS', 'OGC:WFS', 'OGC:WCS'] and in_url(source_url.upper(), ['REQUEST=GETCAPABILITIES']):
		return True
	elif protocol in ['OAI-PMH'] and (in_url(source_url, ['VERB=IDENTIFY']) or in_content(source_content, ['<Identify>'])):
		return True
	elif protocol in ['OpenSearch']	and in_content(source_content, ['OpenSearchDescription']):
		return True
 	elif protocol in ['THREDDS Catalog', 'ISO-19115']:
 		#these just are the descriptions (we can quibble about iso)
 		return True

 	return False




