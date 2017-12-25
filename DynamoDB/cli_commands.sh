# table names are specified in the data-json, there do put-items, delete items.. of different tables
# see myTestTableData.json
aws dynamodb batch-write-item --request-items file://myTestTableData_cli.json --region eu-west-1 --profile franzi
# if error in one command (e.g. table does not exist)s the whole upload is rejected
