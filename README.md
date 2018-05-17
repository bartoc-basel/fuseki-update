### Fuseki CLI Tool
A collection of scripts and utility functions to manage and update a Fuseki2 triple store.

Requires a default.cfg and credentials to the google spreadsheet for this to work.

The main update routine loads values from a google sheets spreadsheet. This file
needs the following columns for each vocabulary which should be loaded into the fuseki triple 
store.

The following input rows are possible. Their order is important:
1. Name of Vocabulary
2. Link to the file (http[s]:// or ftp://)
3. Format of the file (accepts values: TTL, RDF, N3, NT, JSON)
4. Short Name (used for Skosmos config.)
5. Fuseki Graph Name (a valid URI)
6. Standard Language (optional, if given will add language tags to every label)
7. Ready? Fill in with __y__. All other lines will be ignored.
8. Base namespace of the vocabulary.

The script will use the following columns for output on each vocabulary:

9. Number of triples loaded into Fuseki if successful. If this field is empty the upload was not successful. 
If this field is 0 then no triples were uploaded (most likely skosify removed all triples from graph).
10. Type of Error (If something went wrong.)
11. Error Message 
12. Skosmos vocabularies.ttl entry. Do not use as is. Language tags are not correct. 



#### Usage

    pyfuseki default.cfg -all

    pyfuseki default.cfg -s skos

    pyfuseki default.cfg -diff
    
    



