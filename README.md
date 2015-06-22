## Text Processing 

###Preprocessing

XML and text parsing for the pipeline between Nutch/Solr and a triplestore or NLP/ML pipeline.

####Parsing/Extraction Output:

```
{
	"solr_identifier": "",  // sha256 of the source url
	"source_url": "",
	"harvested_date": "",
	"modified_date": "",
	"identity": {
		"protocol": "",  // base type of the response, ex OGC or OAI-PMH
		"service": {  // service type, ex Catalog, WFS
			"name": "",
			"request": "",
			"version": "",
			"language": ""
		}, 
		"dataset": {
			"name": "",
			"request": "",
			"version": "",
			"language": ""
		},
		"metadata": {
			"name": "",
			"request": "",
			"version": "",
			"language": ""
		},
		"resultset": {
			"name": "",
			"request": "",
			"dialect": "",
			"version": "",
			"language": ""
		}
	},
	"service_description": {
		"title": "",
		"description": "", 
		"subjects": [],
		"contact": {},
		"rights": "",
		"language": "",
		"endpoints": [
			{
				"url": "",
				"name": "",
				"description": "",
				"actionable": "",
				"method": "",
				"mimetype": "",
				"format": "",
				"parameters": []
			}
		],
		"parentOf": [],
		"isDescribedBy": ""
	},
	"datasets": [
		{
			"childOf": "",  // reference to the parent service profile
			"title": "",
			"description": "",
			"spatial_extent": "",  // wgs84 WKT string for geosparql support in parliament
			"temporal_extent": {
				"start": "",
				"end": ""
			},
			"subjects": [],
			"rights": "",
			"formats": [],
			"isDescribedBy": ""  // a reference to the metadata record
		}
	],
	"metadata": {
		"describes": "",
		""
	}



	"service": {
		"title": [],
		"abstract": [],
		"source": [],
		"contact": [],
		"rights": [], // access, usage rights (this is conflating a variety of "rights" concepts)
		"language": [],
		"subject": [], // keywords as normalized string and then split
		"endpoints": [
			{
				"type": "", 
				"url": "", 
				"http_method": "", // get | post
				"parameters": [
					// for the parameter descriptions
					{
						"name": "parameter name",
						"namespace": {"uri": "", "prefix": ""},
						"type",
						"format",
						"values": [""]
					}
				]
			}
		]
	}
}
```

Notes:

The service elements are based on the DCTerms supported in the ontology. 

####Currently Supported Service Descriptions

- [x] OpenSearch
- [x] THREDDS Catalog
- [x] OAI-PMH Identify
- [ ] WxS GetCapabilities
- [ ] ATOM (OpenSearch?/GeoRSS?)
- [ ] WADL
- [ ] WSDL

This is contigent on those service types having service-level descriptions. 

####Currently Supported Dataset Descriptions

- [x] ISO 19115
- [ ] FGDC
- [ ] Dif (?)


### Sample Extraction

Pull some set of data from the Solr instance, extract the raw_content, perform some basic text cleanup, extract elements for the high level service description and extract everything else as generic text/attribute object.

####YAML Query Configuration

```yaml
#list of fields to return in the result set
fields:
  - field1
  - field2

#query object for standard solr queries
query:
  field1: value1

#sample set generator to pull some number
#of documents within a limit/offset range 
#structure (return 3 random documents between
#index 0 and 10)
sample:
  start: 0
  end: 10
  size: 3

#output content type
ext: json

#to just run some subsetter (no sampling)
limit: 10
offset: 0

```

Note, this doesn't have anything to reset the range to fall within the result set if you include the sample.


To run:

```
solr.py -s 'xx.xxx.xx.xx' -p '8080' -c 'collection1' -q local/sample.yaml -o local/responses_from_sample.json -U xxxxxx -P xxxxxxx

```
