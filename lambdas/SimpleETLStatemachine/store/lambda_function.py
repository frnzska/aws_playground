import json
import logging
import boto3
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')
def lambda_handler(event, context):
    """Saves file to s3"""
    logger.info(json.dumps(event))
    bucket = os.environ['bucket']
    s3_key = event['s3_key']
    data = json.dumps(event['record']).encode('utf')
    s3.put_object(Bucket=bucket,Key=s3_key, Body=data)
    return event