import json


def hello(event, context):
    body = {
        "message": "Hello, is it me you looking for?",
        "input": event
    }

    response = {
        "statusCode": 200,
        "body": json.dumps(body)
    }

    return response
