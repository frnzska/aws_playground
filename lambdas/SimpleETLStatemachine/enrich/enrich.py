import json
import logging
import uuid
import datetime as dt

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """Sets uuid"""
    event['record']['event_uuid'] = uuid.uuid4()
    today = dt.datetime.now().strftime('%Y/%m/%d')
    event['s3_key'] = '/'.format([event, today])
    logger.info(f'enrich function: {json.dumps(event)}')

    return event

