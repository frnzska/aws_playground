import json
import logging
import uuid


logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """Sets uuid"""
    event['record']['event_uuid'] = uuid.uuid4().hex
    logger.info(f'enrich function: {json.dumps(event)}')

    return event

