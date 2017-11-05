import json
import logging
import boto3
import os
import datetime as dt
import uuid

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')
def lambda_handler(event, context):
    """Saves events to s3 as jsons"""
    logger.info(json.dumps(event))
    bucket = os.environ['bucket']
    today = dt.datetime.now().strftime('%Y/%m/%d')
    _ext_file = uuid.uuid4().hex
    s3_key= '/'.join([event['record']['name'], today, _ext_file]) + '.json'
    data = json.dumps(event['record']).encode('utf')
    s3.put_object(Bucket=bucket,Key=s3_key, Body=data)
    return event
