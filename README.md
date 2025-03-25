# dumparse

Parse MarkLogic support dumps

## install

Just get the .py file.  Fix the path to call Python 3.

## running

Just run for options (very few).

## results

Parses to the same structure/files as the perl parser.

## problems

Let me know.  It's been used a bit so half decent anyway.

## dumparse.xml

### workspace for queries on parsed dumps that have been loaded 

Load via mlcp as, for example,

~/mlcp/mlcp-10.0.6.2/bin/mlcp.sh import -host localhost -port 8000 -username admin -password admin -mode local -input_file_path ./Support-Dump/ -database Documents -output_collections exp

The queries select on collection so you don't need a separate database for each dump.
