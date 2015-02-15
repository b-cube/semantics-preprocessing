import json
from lxml import etree
import re
import glob


files = glob.glob('tests/docs/response_*.json')

pttn = u'^<!\[CDATA\[(.*?)\]\]>$'

parser = etree.XMLParser(encoding="utf-8")

'''
if they are all ascii how is the one in japanese?
'''


def identify(raw_content, url):
    if 'http://www.isotc211.org/2005/gmi' in raw_content or 'http://www.isotc211.org/2005/gmd' in raw_content:
        return 'ISO 19115:2003/19139'
    elif 'http://www.unidata.ucar.edu/namespaces/thredds/InvCatalog/v1.0' in raw_content:
        return 'THREDDS'
    elif 'http://xml.opendap.org/ns/DAP2' in raw_content:
        return 'OPeNDAP:OPeNDAP'
    elif 'http://a9.com/-/spec/opensearch/1.1/' in raw_content:
        return 'OpenSearch1.1'
    elif 'http://wadl.dev.java.net' in raw_content:
        return 'WADL'
    elif 'http://schemas.xmlsoap.org/wsdl/' in raw_content:
        return 'WWW:WSDL'
    elif 'http://www.w3.org/2005/Atom' in raw_content:
        '''
        note: this can be some combination of atom, opensearch, and georss content
        '''
        return 'ATOM'
    elif 'http://www.opengis.net/wms' in raw_content or 'SERVICE=WMS' in url.upper() \
            or ('http://mapserver.gis.umn.edu/mapserver' in raw_content and 'SERVICE=WMS' in url.upper()):
        return 'OGC:WMS'
    elif 'http://www.opengis.net/wmts/1.0' in raw_content:
        return 'OGC:WMTS'
    elif 'http://www.opengis.net/wfs' in raw_content or 'SERVICE=WFS' in url.upper() or \
            ('http://mapserver.gis.umn.edu/mapserver' in raw_content and 'SERVICE=WFS' in url.upper()):
        return 'OGC:WFS'
    elif 'http://www.opengis.net/wcs' in raw_content or 'SERVICE=WCS' in url.upper() \
            or ('http://mapserver.gis.umn.edu/mapserver' in raw_content and 'SERVICE=WCS' in url.upper()):
        return 'OGC:WCS'
    elif 'http://www.opengis.net/swe/1.0.1' in raw_content:
        return 'OGC:SWE'
    elif 'http://gcmd.gsfc.nasa.gov/Aboutus/xml/dif/' in raw_content:
        return 'DIF'
    elif 'http://www.openarchives.org/OAI/' in raw_content:
        # OAI-PMH as Dublin Core
        return 'OAI-PMH'
    elif 'http://pds.nasa.gov/pds4/pds/v1' in raw_content:
        return 'PDS'
    elif 'http://www.loc.gov/MARC21/slim' in raw_content:
        # just for excel, we hate excel
        return 'MARC21-std'
    elif '<metstdv>FGDC-STD-001-1998' in raw_content:
        return 'FGDC-1998'
    elif '<metstdv>FGDC-STD-012-2002' in raw_content:
        return 'FGDC-2002'
    elif 'http://www.incident.com/cap/1.0' in raw_content or 'urn:oasis:names:tc:emergency:cap:' in raw_content:
        '''
        usgs alerts
            view-source:http://www.usgs.gov/alerts/cap/USGS-landslides.20060831T184846
        '''
        return 'CAP-ALERT'
    elif 'http://earth.google.com/kml' in raw_content:
        # note: ignoring the version here (don't really care for ID)
        return 'KML'
    elif 'http://www.esri.com/schemas/ArcGIS/9.2' in raw_content:
        return 'ArcGISExplorerDocument'
    elif 'urn:schemas-microsoft-com:office:office' in raw_content:
        return 'MS Office'
    elif 'http://www.unidata.ucar.edu/namespaces/netcdf/ncml-2.2' in raw_content:
        return 'NetCDF'
    elif '<rss version="' in raw_content or 'http://api.npr.org/nprml' in raw_content or 'rss' in url:
        return 'RSS'
    elif 'http://archipelago.phrasewise.com/rsd' in raw_content or '?rsd' in url or 'rsd.xml' in url:
        return 'WordPress'
    elif 'http://www.loc.gov/METS_Profile/' in raw_content:
        return 'LOC-METS'
    elif 'http://datacite.org/schema/' in raw_content:
        return 'DataCite'
    elif 'eml://ecoinformatics.org/eml-' in raw_content:
        return 'EML'
    elif 'http://anss.org/xmlns/catalog/0.1' in raw_content or 'http://anss.org/xmlns/tensor/0.1' in raw_content or 'http://quakeml.org/xmlns/bed/1.2' in raw_content:
        return 'QuakeML1.2'
    elif 'http://niem.gov/' in raw_content:
        return 'Niem (Foia)'
    elif 'http://schemas.xmlsoap.org/disco/' in raw_content:
        return 'Disco'
    elif 'http://schemas.xmlsoap.org/soap/envelope/' in raw_content:
        return 'Soap'
    elif 'http://www.google.com/geo/schemas/sitemap/1.0' in raw_content or 'http://www.sitemaps.org/schemas/sitemap/' in raw_content:
        return 'Sitemap'
    elif 'http://www.itunes.com/dtds/podcast-1.0.dtd' in raw_content:
        return 'iTunes'
    elif 'http://www.cuahsi.org/waterML/' in raw_content:
        return 'WaterML'
    elif 'http://echo.nasa.gov/' in raw_content:
        return 'ECHO'
    elif 'http://modapsws.gsfc.nasa.gov/xsd' in raw_content:
        return 'MODAPS'
    elif 'http://www.noaa.gov/ioos/' in raw_content:
        return 'IOOS'
    elif 'http://www.opengis.net/' in raw_content:
        return 'Unidentified OGC'

    return ''



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

    #try to grok what it is
    data_service = identify(raw_content, data['id'])

    if data_service:
        with open('identified_nutch_namespaces.csv', 'a') as g:
            g.write('|'.join([data['digest'], data['id'].replace('|', '$$'), data_service]) + '\n')
    else:
        #let's put in another list for reparsing

        repacked = []
        for p, n in namespaces.iteritems():
            repacked.append('|'.join([data['digest'], data['id'], (p if p else 'default'), n]))

        with open('unidentified_nutch_namespaces.csv', 'a') as g:
            g.write('\n'.join(repacked) + '\n')


