import boto3
import logging
import json
import base64

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')


def get_data_from_s3(lambda_event):
     """
    Read data from S3
    :param lambda_event: event send on file upload on s3 invoking lambda
    :return: list of events
    """

     bucket = lambda_event['Records'][0]['s3']['bucket']['name']
     obj_key = lambda_event['Records'][0]['s3']['object']['key']
     logger.info(f'Get file {bucket}/{obj_key}')
     try:
         s3_obj = s3.get_object(Bucket=bucket, Key=obj_key)
     except Exception as e:
         logger.error(f'S3 file load failed of {bucket}/{obj_key}', exc_info=True)
         raise e
     logger.info('extract data from s3 obj')
     data = s3_obj['Body'].read().decode('utf-8')
     events = data.split('\n')
     if events[-1] == '':
         events = events[:-1]
     return events

def get_kinesis_stream_events(lambda_event):
    """
    Get data records from Kinesis
    :param lambda_event: lambda function event
    :return: list(dict)
    """
    records = lambda_event['Records']
    events = [base64.b64decode(record['kinesis']['data']).decode('utf-8') for record in records]
    events = [json.loads(e) for e in events]
    return events
