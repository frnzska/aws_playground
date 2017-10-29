import json
import logging
import jsonschema

logger = logging.getLogger()
logger.setLevel(logging.INFO)

json_validation_schema = {
  "$schema": "http://json-schema.org/draft-06/schema#",
  "description": "schema for a event that can be sifted",
  "required": ["name", "version"],
  "properties": {
    "name": {
      "oneOf": [
        {"type": "string", "pattern": "^user:+"},
        {"type": "string", "pattern": "^logs:+"}
      ]
    }
  }
}


def lambda_handler(event, context):
    logger.info(json.dumps(event))
    try:
        jsonschema.validate(event, json_validation_schema)
        return event
    except jsonschema.ValidationError:
        logger.exception("Invalid event")
        return None
