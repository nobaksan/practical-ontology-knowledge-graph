curl -u admin:admin -X POST 'http://localhost:3030/$/datasets' \
     --data 'dbName=onto&dbType=tdb2'
curl -u admin:admin -X POST -H 'Content-Type: text/turtle; charset=utf-8' \
     --data-binary @실행_환경/검증_근거/enterprise_ontology.ttl \
     'http://localhost:3030/onto/data?default'
