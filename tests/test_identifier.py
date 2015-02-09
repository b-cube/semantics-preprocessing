import unittest
import os
import json

from lib.identifier import *

class TestIdentifier(unittest.TestCase):
    def setUp(self):
    	'''
		no setup
    	'''
    	pass

    def test_in_url(self):
    	should_be_in_url = in_url('http://ferret.pmel.noaa.gov/thredds/wcs/las/woa01_annual/data_ferret.pmel.noaa.gov_thredds_dodsC_data_PMEL_WOA01_english_annual_O2sat_ann_stddev_1deg.nc.jnl?service=WCS&version=1.0.0&request=GetCapabilities', ['service=WCS'])
    	should_not_be_in_url = in_url('http://mrdata.usgs.gov/wfs/digitized?request=getcapabilities&service=WFS&version=1.1.0', ['service=WCS'])

    	self.assertTrue(should_be_in_url)
    	self.assertFalse(should_not_be_in_url)

    def test_in_content(self):
    	test_content = '''<?xml version="1.0" encoding="UTF-8"?>
<WMS_Capabilities version="1.3.0"
  xmlns="http://www.opengis.net/wms"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xmlns:esri_wms="http://www.esri.com/wms"
  xsi:schemaLocation="http://www.opengis.net/wms http://schemas.opengis.net/wms/1.3.0/capabilities_1_3_0.xsd http://www.esri.com/wms http://egisws02.nos.noaa.gov/ArcGIS/services/NMFS/EFHAreasProtectedFromFishing/MapServer/WMSServer?version=1.3.0&amp;service=WMS&amp;request=GetSchemaExtension">
  <Service>
    <Name><![CDATA[WMS]]></Name>
    <Title><![CDATA[NMFS_EFHAreasProtectedFromFishing]]></Title>
    <Abstract>WMS</Abstract>
    <KeywordList><Keyword><![CDATA[]]></Keyword></KeywordList>
    <OnlineResource xmlns:xlink="http://www.w3.org/1999/xlink" xlink:type="simple" xlink:href="http://egisws02.nos.noaa.gov/ArcGIS/services/NMFS/EFHAreasProtectedFromFishing/MapServer/WMSServer"/>
    <ContactInformation>
      <ContactPersonPrimary>
        <ContactPerson><![CDATA[]]></ContactPerson>
        <ContactOrganization><![CDATA[]]></ContactOrganization>
      </ContactPersonPrimary>'''
    	should_be_in_content = in_content(test_content, ['http://www.opengis.net/wms'])
    	should_not_be_in_content = in_content(test_content, ['http://www.opengis.net/wfs'])
    	
    	self.assertTrue(should_be_in_content)
    	self.assertFalse(should_not_be_in_content)

    def test_identify(self):
    	thredds_catalog = '''<?xml version="1.0" encoding="UTF-8"?>
    <thredds:catalog xmlns:fn="http://www.w3.org/2005/02/xpath-functions"
                 xmlns:thredds="http://www.unidata.ucar.edu/namespaces/thredds/InvCatalog/v1.0"
                 xmlns:xlink="http://www.w3.org/1999/xlink"
                 xmlns:bes="http://xml.opendap.org/ns/bes/1.0#">
   <thredds:service name="dap" serviceType="OPeNDAP" base="/opendap/hyrax"/>
   <thredds:service name="file" serviceType="HTTPServer" base="/opendap/hyrax"/>
        <thredds:dataset name="/TRMM_3Hourly_3B42/1997/365"
                    ID="/opendap/hyrax/TRMM_3Hourly_3B42/1997/365/">'''
        test_protocol = identify_protocol(thredds_catalog, 'view-source:http://disc2.nascom.nasa.gov/opendap/TRMM_3Hourly_3B42/1997/365/catalog.xml')

        self.assertTrue(test_protocol == 'THREDDS Catalog')

        oaipmh_catalog = '''
		<?xml version="1.0" encoding="UTF-8" ?>
<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd">
    <responseDate>2015-02-09T16:17:39Z</responseDate>
    <request verb="Identify">http://aura.abdn.ac.uk/dspace-oai/request</request>
    <Identify>
        <repositoryName>Aberdeen University Research Archive</repositoryName>
        <baseURL>http://aura.abdn.ac.uk/dspace-oai/request</baseURL>
        <protocolVersion>2.0</protocolVersion>
        '''

        test_protocol = identify_protocol(oaipmh_catalog, 'http://aura.abdn.ac.uk/dspace-oai/request?verb=Identify')
        self.assertTrue(test_protocol == 'OAI-PMH')


        wcs_capabilities = '''
<?xml version="1.0" encoding="UTF-8"?>
<WCS_Capabilities xmlns="http://www.opengis.net/wcs" xmlns:gml="http://www.opengis.net/gml" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.0.0" updateSequence="1.0" xsi:schemaLocation="http://www.opengis.net/wcs http://schemas.opengis.net/wcs/1.0.0/wcsCapabilities.xsd">
   <Service>
      <description>GeoBrain Web Coverage Server for DEM data</description>
      <name>Geobrain_WCS_DEM</name>
      <label>GMU LAITS Web Coverage Server</label>
      <keywords>
         <keyword>GMU LAITS GeoBrain WCS DEM</keyword>
      </keywords>
        '''
        test_protocol = identify_protocol(test_protocol, 'http://geobrain.laits.gmu.edu/cgi-bin/gbwcs-dem?service=wcs&version=1.1.0&request=getcapabilities&coverage=SRTM_90m_Global,SRTM_30m_USA,GTOPO_30arc_Global')
        self.assertFalse(test_protocol == 'OGC:WFS')
        self.assertTrue(test_protocol == 'OGC:WCS')

    def test_is_service_description(self):
    	test_protocol = 'OGC:WFS'
    	test_content = '''
<WFS_Capabilities 
   version="1.0.0" 
   updateSequence="0" 
   xmlns="http://www.opengis.net/wfs" 
   xmlns:ogc="http://www.opengis.net/ogc" 
   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
   xsi:schemaLocation="http://www.opengis.net/wfs http://schemas.opengis.net/wfs/1.0.0/WFS-capabilities.xsd">
    	'''
    	test_url = 'http://mrdata.usgs.gov/services/akages-geo?request=getcapabilities&service=WFS&version=1.0.0'

    	is_svc = is_service_description(test_protocol, test_content, test_url)
    	self.assertTrue(is_svc)

    	test_protocol = 'OAI-PMH'
    	test_content = '''
<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd">
    <responseDate>2015-02-09T16:17:39Z</responseDate>
    <request verb="Identify">http://aura.abdn.ac.uk/dspace-oai/request</request>
    <Identify>
        <repositoryName>Aberdeen University Research Archive</repositoryName>
        <baseURL>http://aura.abdn.ac.uk/dspace-oai/request</baseURL>
        <protocolVersion>2.0</protocolVersion>
    	'''
    	test_url = 'http://aura.abdn.ac.uk/dspace-oai/request?verb=Identify'

    	is_svc = is_service_description(test_protocol, test_content, test_url)
    	self.assertTrue(is_svc)





