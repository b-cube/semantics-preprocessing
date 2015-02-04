#!/anaconda/bin/python

import os
import argparse
import json
import codecs
import re
import sys


import yaml

'''
base nutch/solr response parser
'''

class FileParser():
	'''
	from a file, return a tuple of id, date, raw_content
	objects from sample data file (basically a json solr response
		untouched from the solr cli)
	'''

	_pttn = u'^<!\[CDATA\[(.*?)\]\]>$'

	def __init__(self):
		pass

	def parse_file(self, file_path):

		assert os.path.exists(file_path)

		with open(file_path, 'r') as f:
			text = f.read()

		response = json.loads(text)
		return [(j['id'], j['date'], j['raw_content']) for j in response['responses']['docs']]

	
	def prepare_raw_content(self, raw_content):
		'''
		string from the solr raw_content element, unmodified
		'''	

		#unicode escape for solr (cdata pattern matching fails without)
		raw_content = raw_content.encode('unicode_escape')

		m = re.search(self._pttn, raw_content)

		assert m

		return m.group(1)

	#TODO: This might turn into a much larger thing (combinations of namespaces, etc)
	def identify_response_type(self, prepared_content, url):
		'''
		let's try to identify what kind of service response it 
		is based on the namespaces

		PRIORITY:
			opensearch
			opensearch esip
			thredds catalog
			OAI-PMH
			iso
			ogc getcapabilities
			wadl
		'''

		if 'http://www.isotc211.org/2005/gmi' in prepared_content or 'http://www.isotc211.org/2005/gmd' in prepared_content:
			return 'ISO'
		elif 'http://www.unidata.ucar.edu/namespaces/thredds/InvCatalog/v1.0' in prepared_content:
			return 'THREDDS'
		elif 'http://xml.opendap.org/ns/DAP2' in prepared_content:
			return 'OpenDap'
		elif 'http://a9.com/-/spec/opensearch/1.1/' in prepared_content:
			return 'OpenSearch'
		elif 'http://wadl.dev.java.net' in prepared_content:
			return 'WADL'
		elif 'http://schemas.xmlsoap.org/wsdl/' in prepared_content:
			return 'WSDL'
		elif 'http://www.w3.org/2005/Atom' in prepared_content:
			'''
			note: this can be some combination of atom, opensearch, and georss content
			'''
			return 'ATOM'
		elif 'http://www.opengis.net/wms' in prepared_content or 'SERVICE=WMS' in url.upper() or ('http://mapserver.gis.umn.edu/mapserver' in prepared_content and 'SERVICE=WMS' in url.upper()):
			return 'WMS'
		elif 'http://www.opengis.net/wmts/1.0' in prepared_content:
			return 'WMTS'
		elif 'http://www.opengis.net/wfs' in prepared_content or 'SERVICE=WFS' in url.upper() or ('http://mapserver.gis.umn.edu/mapserver' in prepared_content and 'SERVICE=WFS' in url.upper()):
			return 'WFS'
		elif 'http://www.opengis.net/wcs' in prepared_content or 'SERVICE=WCS' in url.upper() or ('http://mapserver.gis.umn.edu/mapserver' in prepared_content and 'SERVICE=WCS' in url.upper()):
			return 'WCS'
		elif 'http://www.opengis.net/swe/1.0.1' in prepared_content:
			return 'SWE'
		elif 'http://gcmd.gsfc.nasa.gov/Aboutus/xml/dif/' in prepared_content:
			return 'DIF'
		elif 'http://www.openarchives.org/OAI/' in prepared_content:
			#OAI-PMH as Dublin Core
			return 'OAI-PMH'
		elif 'http://pds.nasa.gov/pds4/pds/v1' in prepared_content:
			return 'PDS'
		elif 'http://www.loc.gov/MARC21/slim' in prepared_content:
			#just for excel, we hate excel
			return 'MARC21-std'
		elif '<metstdv>FGDC-STD-001-1998' in prepared_content:
			return 'FGDC-1998'
		elif '<metstdv>FGDC-STD-012-2002' in prepared_content:
			return 'FGDC-2002'
		elif 'http://www.incident.com/cap/1.0' in prepared_content or 'urn:oasis:names:tc:emergency:cap:' in prepared_content:
			'''
			usgs alerts
				view-source:http://www.usgs.gov/alerts/cap/USGS-landslides.20060831T184846
			'''
			return 'CAP-ALERT'
		elif 'http://earth.google.com/kml' in prepared_content:
			#note: ignoring the version here (don't really care for ID)
			return 'KML'
		elif 'http://www.esri.com/schemas/ArcGIS/9.2' in prepared_content:
			return 'ArcGISExplorerDocument'
		elif 'urn:schemas-microsoft-com:office:office' in prepared_content:
			return 'MS Office'
		elif 'http://www.unidata.ucar.edu/namespaces/netcdf/ncml-2.2' in prepared_content:
			return 'NetCDF'
		elif '<rss version="' in prepared_content or 'http://api.npr.org/nprml' in prepared_content or 'rss' in url:
			return 'RSS'	
		elif 'http://archipelago.phrasewise.com/rsd' in prepared_content or '?rsd' in url or 'rsd.xml' in url:
			return 'WordPress'	
		elif 'http://www.loc.gov/METS_Profile/' in prepared_content:
			return 'LOC-METS'
		elif 'http://datacite.org/schema/' in prepared_content:
			return 'DataCite'
		elif 'eml://ecoinformatics.org/eml-' in prepared_content:
			return 'EML'
		elif 'http://anss.org/xmlns/catalog/0.1' in prepared_content or 'http://anss.org/xmlns/tensor/0.1' in prepared_content or 'http://quakeml.org/xmlns/bed/1.2' in prepared_content:
			return 'USGS Quake'
		elif 'http://niem.gov/' in prepared_content:
			return 'Niem (Foia)'
		elif 'http://schemas.xmlsoap.org/disco/' in prepared_content:
			return 'Disco'
		elif 'http://schemas.xmlsoap.org/soap/envelope/' in prepared_content:
			return 'Soap'
		elif 'http://www.google.com/geo/schemas/sitemap/1.0' in prepared_content or 'http://www.sitemaps.org/schemas/sitemap/' in prepared_content:
			return 'Sitemap'
		elif 'http://www.itunes.com/dtds/podcast-1.0.dtd' in prepared_content:
			return 'iTunes'
		elif 'http://www.cuahsi.org/waterML/' in prepared_content:
			return 'WaterML'
		elif 'http://echo.nasa.gov/' in prepared_content:
			return 'ECHO'
		elif 'http://modapsws.gsfc.nasa.gov/xsd' in prepared_content:
			return 'MODAPS'
		elif 'http://www.noaa.gov/ioos/' in prepared_content:
			return 'IOOS'
		elif 'http://www.opengis.net/' in prepared_content:
			return 'Unidentified OGC'

		return ''


