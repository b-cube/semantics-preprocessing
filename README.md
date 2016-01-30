## Semantics Preprocessing 

Contains the core data processing code for the BCube document characterization effort. For the most part, the functionality is demonstrated through the semantics_pipeline task definitions or through the Response-Identification-Info notebooks. 


####Document Identification

This process currently relies on a predefined set of rules. These are provided as is and we make no claims of 100% accuracy.

Brief aside - IANA-style magic numbers don't exist for XML standards/specifications. Looking across just the well known standards used in the geoscience community, that kind of short and understandable flag is difficult to provide in a way that considers a standard as a single representation, ie an FGDC-CSDGM record, an embedded standard such as those found in an OAI-PMH ListRecords or GetRecordByID response, or a blended document combining multiple standards in a non-standard way. Keying on namespaces or the root element tag alone is increasingly problematic in this space. That being said, the provided identification rules are themselves a source of potential mismatch but a) we need to start somewhere and b) these can be used to understand the kinds of features and training set needed for modeling.

Onward.

The rulesets are found in `semproc/configs` and named as `{standard}_identifier.yaml`. You can have one large YAML file, containing all of the rulesets you'd like to use, or create separate files (here for legibility). 

Main configuration structure:

```
- name: # the unique name of the standard/specification or a unique
        # name for the suite of documents supported by a standard
  {metadata | service | dataset | resultset}: # use a key value based on the type of document described within
    - name: # a unique name for the document type within the standard/specification
      dialect: # should the parent key be resultset, this object can be used to identify the child standard/specification
      	text: # name of the child standard
        # OR
        checks: {same structure as described below, if the dialect type is provided as an element or item}
      request: # should the parent key be service, the request text should be the name of the method, for example, GetCapabilities for an OGC request.
      filters: {array of filter definitions, see Filters below. These are the main document rules.}
      versions: {array of version definitions, see Versions below. The rules for identifying the document version.}
      language: {array of language definitions, see Language below. The rules for identifying the language of the document.}
      errors: {array of error definitions, see Errors below. The rules for identifying if the document is an error response.}
```

XPath rules should not be namespaced and are limited to the XPath options supported by lxml. See the included configurations for examples of XPath rules.

**NOTE:** some of these objects can be reused. For example, `filters` can be used whenever a ruleset definition is required. For version, langauge and error objects, filters is superceded by `defaults` and/or `checks`. `defaults` is a list of rules that checks for the existence of the item defined by the `value` and supplies the text value to use. So if the pattern in `value` is matched, the version is the value of the `text` element. `checks` is a list of rules used to extract the desired value, ie, the language is the value at the provided XPath location. Both structures can be provided within one of these elements; all matches are returned. 

**Filters**

This contains the array of rules for identifying a specific document or object. These are existence checks except when used the structure is used as part of a `checks` object. 

```
filters:
  {ors | ands}: # match any one vs. match all
  	- type: {simple | xpath | complex } # simple for a basic CONTAINS text match, xpath for an existence of item(s) or text check, complex if the ruleset requires another level of filters (see below for details)
  	  object: {content | url} # flag for denoting which text object to use, the document content or the document source URL
  	  value: the string or XPath for the match process
  	  text: # required if (and only if) part of a defaults block
```

Using `complex`

A complex filter type handles situations where you need to combine an AND set with an OR set. For example, a document must contain the string 'xmlns="http://example.com/namespace"' and one of any of these strings, 'MetadataID' or 'MetadataVersion' or 'SpatialResolution'. You would include two filter rules, both using the 'complex' type, one for the AND and one for the OR.

```
- type: complex
  operator: {ands | ors} # match one vs. match all
  filters: {same filter structure as previously described}
```

**Versions**

This object contains the ruleset for identifying the version information.

```
versions:
  checks: {}
  defaults: {}
```

**Language**

This object contains the ruleset for identifying the langauge of the documnet. In some cases, the response content headers and the language used with the response don't match. 

```
language:
  checks: {}
  defaults: {}
```

**Errors**

This object contains the ruleset for identifying if the document is returning an error message. In some cases, a standard/specification encodes invalid requests or other types of exceptions as valid documents (ie returns 200 - OK) but containing a description of the error. This is useful for identifying improvements to the access client but not for formal characterization of the document.

```
errors:
  checks: {}
  defaults: {}
```

####Bag of Words and Unique Identifier Exclusions

The `semproc/corpus` directory contains a set of files that can be used for excluding tokens during the bag of words extraction process. This includes namespace URLs, mimetypes, and known text patterns such as scheme definitions. These files can be updated as necessary; however, the module must be rebuilt before next run. 



