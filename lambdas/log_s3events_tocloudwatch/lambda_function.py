import logging
import cfnresponse
import os
import boto3
import json

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.debug('Loading function')

client = boto3.client('cloudformation')


def lambda_handler(event, context):
    key, val = 'LogicalResourceId', 'functionInvocation'
    if key in event and event[key] == val:
        response = client.describe_stacks(StackName=os.environ['STACK_NAME'])
        response_info = {}
        response_info['Data'] = response['Stacks'][0]['StackId']
        cfnresponse.send(event, context, cfnresponse.SUCCESS, response_info)
    logger.info('LogS3DataEvents')
    logger.info(json.dumps(event))
    return event