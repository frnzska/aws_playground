import boto3
import json
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class Json2DynamoDB:

    def __init__(self, *, table_name):
        self.table_name = table_name
        dynamoDB = boto3.resource('dynamodb', region_name='eu-west-1')
        self.table = dynamoDB.Table(table_name)

    def upload_file_items(self, *, json_file):
        with open(json_file) as f:
            items = json.load(f)
            for item in items:
                self.table.put_item(
                    Item={
                        'id': item['id'],
                        'user_name': item['user_name'],
                        'display_name': item['display_name'],
            }
        )

dynamo = Json2DynamoDB(table_name='myTestTable')
dynamo.upload_file_items(json_file='DynamoDB/myTestTableData.json')
print(dynamo.table.get_item(Key={'id': 2, 'user_name': 'Sue'}))


# Query and Scan:
#----------------
# conditions like equals (eq), lessthan (lt).. can be found
# at http://boto3.readthedocs.io/en/latest/_modules/boto3/dynamodb/conditions.html
from boto3.dynamodb.conditions import Key, Attr
response = dynamo.table.query(
    KeyConditionExpression=Key('id').eq(3)
)
print(response['Items'])
# >> [{'user_name': 'Karl', 'display_name': 'karl', 'id': Decimal('3')}]


response = dynamo.table.scan(
    FilterExpression=Attr('user_name').begins_with('K') | Attr('user_name').begins_with('k')
)
print(response['Items'])
# >> [{'user_name': 'Karl', 'display_name': 'karl', 'id': Decimal('3')},
#     {'user_name': 'Karoline', 'display_name': 'karo', 'id': Decimal('4')}]

response = dynamo.table.scan(
    FilterExpression=Attr('display_name').contains('aro')
)
print(response['Items'])
# >> [{'user_name': 'Karoline', 'display_name': 'karo', 'id': Decimal('4')}]
