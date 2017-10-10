import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    text = 'Hi ' +  event['who']
    logger.info(text)
    return text