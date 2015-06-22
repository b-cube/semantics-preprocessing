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
				"parameters": [],
				"status": "",  // for reference re: the triples later (this may not be in the JSON)
				"status_checked": ""  // for reference re: the triples later (this may not be in the JSON)
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
			"isDescribedBy": "",  // a reference to the metadata record(s)
			"parameters": [],
			"endpoints": []  // see the previously described endpoint
		}
	],
	"metadata": {
		"describes": "",  // some reference 
		"parentOf": "",  // for a ds record, we have the Mx series info
		"childOf": "",  // for a ds record, include a metadata object linked to the seriesMetadata
		"title": "",
		"description": "",
		"subjects": [],
		"spatial_extent": "",  // wgs84 WKT string for geosparql support in parliament
		"temporal_extent": {
			"start": "",
			"end": ""
		},
		"contact": {}, 
		"rights": "",
		"language": "",
		"endpoints": []  // see the previously described endpoint
	}
}
```

Notes:

The service elements are based on the DCTerms supported in the ontology. 


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
