#Pipeline Workflows


The workflow manager assumes that you are running the pipeline on some set of files for bulk processing. The supported workflows are built with standard inputs, as are most of the tasks. 

The parameters:

- workflow: the name of the workflow to execute
- interval: number of files per chunk (the dependency trees become a problem, locally certainly, so we're batch processing the batch processor).
- config: the file path to the task runner YAML file
- directory: the file path to the input directory for the documents to process. Right now, those are the Solr docs as JSON files, one per.
- start: start index for the chunking
- end: end index for the chunking


### Notes

This assumes that **any** input directory contains JSON files.

