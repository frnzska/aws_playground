import json
import logging
import uuid

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """Sets uuid"""
    event['event_uuid'] = uuid.uuid4()
    event['s3_key'] = ''#TODOt
    logger.info('enrich function: ', event)

    return event

