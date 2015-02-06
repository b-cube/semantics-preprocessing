from lxml import etree

'''
spatial handling:
	wcs envelopes
'''
def parse_gml_envelope(envelope, namespaces):
	'''
	from a wcs lonLatEnvelope node, extract a bbox as 
	[min, miny, maxx, maxy] with crs understanding

	note: no reprojection here so if not epsg:4326?
	'''
	srs = envelope.attrib['srsName'] if 'srsName' in envelope.attrib
	if srs != 'EPSG:4326':
		return []

	#two nodes required, first as lower left, second as upper right
	lower_left = envelope.xpath('gml:pos[1]', namespaces=namespaces)
	assert lower_left
	mins = map(float, lower_left[0].text.split(' '))

	upper_right = envelope.xpath('gml:pos[2]', namespaces=namespaces)
	assert upper_right
	maxes = map(float, upper_right[0].text.split(' '))

	return mins + ,axes