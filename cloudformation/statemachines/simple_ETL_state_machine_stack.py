from troposphere import Ref, iam, awslambda, GetAtt, Base64, Join, stepfunctions, Sub
from troposphere import Template
from awacs.aws import Statement, Action, Allow
import boto3
import ruamel_yaml as yaml
from pkg_resources import resource_string
import json
import yaml



cfg = yaml.load(resource_string('cloudformation', 'config.yml'))

STACK_NAME = cfg['simple_ETL_state_machine']['STACK_NAME']
FUNCTION_NAME_VALIDATE = cfg['simple_ETL_state_machine']['FCT_VALIDATE']
DEPLOYMENT_BUCKET = cfg['simple_ETL_state_machine']['DEPLOYMENT_BUCKET']
S3_KEY_VALIDATE = cfg['simple_ETL_state_machine']['S3_KEY_VALIDATE']
FUNCTION_NAME_ENRICH = cfg['simple_ETL_state_machine']['FCT_ENRICH']
S3_KEY_ENRICH = cfg['simple_ETL_state_machine']['S3_KEY_ENRICH']
FUNCTION_NAME_STORE = cfg['simple_ETL_state_machine']['FCT_STORE']
S3_KEY_STORE = cfg['simple_ETL_state_machine']['S3_KEY_STORE']

template = Template()
description = 'Template for simple ETL state machine'
template.add_description(description)
template.add_version('2010-09-09')


#### IAM for lambda ####
lambda_execution_role = template.add_resource(iam.Role(
    "LambdaExecutionRole",
    Path="/",
    Policies=[
        iam.Policy(
            PolicyName='GrantLogs',
            PolicyDocument={
                "Version": "2012-10-17",
                "Statement": [
                    Statement(
                        Sid='Logs',
                        Effect=Allow,
                        Action=[
                            Action('logs', '*')
                        ],
                        Resource=["arn:aws:logs:*:*:*"]
                    ),
                ]
            }),
        iam.Policy(
            PolicyName='GrantS3',
            PolicyDocument={
                "Version": "2012-10-17",
                "Statement": [
                    Statement(
                        Sid='S3Access',
                        Effect=Allow,
                        Action=[
                            Action('s3', 'Get*'),
                            Action('s3', 'List*'),
                            Action('s3', 'PutObject')
                        ],
                        Resource=["*"]
                    ),
                ]
            }),
    ],
    AssumeRolePolicyDocument={
            "Version": "2012-10-17",
            "Statement": [{
                "Action": ["sts:AssumeRole"],
                "Effect": "Allow",
                "Principal": {
                    "Service": ["lambda.amazonaws.com"]
                }
            }]
        },
    )
)

#### IAM for statemachine ####
state_execution_role = template.add_resource(iam.Role(
    "StateExecutionRole",
    Policies=[
        iam.Policy(
            PolicyName='StatesExecutionPolicy',
            PolicyDocument={
                "Version": "2012-10-17",
                "Statement": [
                    Statement(
                        Sid='Logs',
                        Effect=Allow,
                        Action=[
                            Action('lambda', 'InvokeFunction')
                        ],
                        Resource=["*"]
                    ),
                ]
            }),
    ],
    AssumeRolePolicyDocument={
            "Version": "2012-10-17",
            "Statement": [{
                "Action": ["sts:AssumeRole"],
                "Effect": "Allow",
                "Principal": {
                    "Service": ["states.eu-west-1.amazonaws.com"],
                }
            }]
        },

))

### Lambda fct ###
validate_fct = template.add_resource(
    awslambda.Function(
        'ValidateFct',
        FunctionName=FUNCTION_NAME_VALIDATE,
        Description='Lambda 1 for Simple ETL Statemachine',
        Handler='validate.lambda_handler',
        Role=GetAtt('LambdaExecutionRole', 'Arn'),
        Code=awslambda.Code(
            S3Bucket=DEPLOYMENT_BUCKET,
            S3Key=S3_KEY_VALIDATE,
        ),
        Runtime='python3.6',
        Timeout='30',
        MemorySize=128
    )
)

enrich_fct = template.add_resource(
    awslambda.Function(
        'EnrichFct',
        FunctionName=FUNCTION_NAME_ENRICH,
        Description='Enrich fct for Simple ETL Statemachine',
        Handler='enrich.lambda_handler',
        Role=GetAtt('LambdaExecutionRole', 'Arn'),
        Code=awslambda.Code(
            S3Bucket=DEPLOYMENT_BUCKET,
            S3Key=S3_KEY_ENRICH,
        ),
        Runtime='python3.6',
        Timeout='30',
        MemorySize=128
    )
)

store_fct = template.add_resource(
    awslambda.Function(
        'StoreFct',
        FunctionName=FUNCTION_NAME_STORE,
        Description='Enrich fct for Simple ETL Statemachine',
        Handler='store.lambda_handler',
        Role=GetAtt('LambdaExecutionRole', 'Arn'),
        Code=awslambda.Code(
            S3Bucket=DEPLOYMENT_BUCKET,
            S3Key=S3_KEY_STORE,
        ),
        Runtime='python3.6',
        Timeout='30',
        MemorySize=128,
        Environment = awslambda.Environment('LambdaVars', Variables={'bucket': 'franziska-adler-test-bucket'})
    )
)

definition_str = json.dumps({
  "StartAt": "Validate",
  "States": {
      "Validate": {
          "Type": "Task",
          "Resource": ':'.join(['arn:aws:lambda:eu-west-1:369667221252:function', FUNCTION_NAME_VALIDATE]),
          "Catch": [{
              "ErrorEquals": ["TypeError"],
              "Next": "Done"
          }],
          "Next": "ChoiceState"
        },
     "ChoiceState":{
        "Type": "Choice",
            "Choices": [
                {
                    "Variable": "$.record.name",
                    "StringEquals": "user:created",
                    "Next": "Enrich"
                },
            ],
           "Default": "Store"
      },
     "Enrich": {
         "Type": "Task",
         "Resource": ':'.join(['arn:aws:lambda:eu-west-1:369667221252:function', FUNCTION_NAME_ENRICH]),
         "Next": "Store",
     },
     "Store":  {
         "Type": "Task",
         "Resource": ':'.join(['arn:aws:lambda:eu-west-1:369667221252:function', FUNCTION_NAME_STORE]),
         "Next": "Done"
     },
     "Done": {
            "Type": "Pass",
            "End": True
     }
  }
})

statemachine = template.add_resource(
    stepfunctions.StateMachine(
        'SimpleETLStateMachine',
        DependsOn= ['StoreFct', 'EnrichFct', 'ValidateFct'],
        DefinitionString = definition_str,
        RoleArn = GetAtt('StateExecutionRole', 'Arn')
    )
)

### build stack
t_json = template.to_json(indent=4)

# ----- Stack Args ----- #

stack_args = {
    'StackName': STACK_NAME,
    'TemplateBody': template.to_json(indent=4),
    'Capabilities': ['CAPABILITY_IAM'],
}

cfn = boto3.client('cloudformation')
print(t_json)
cfn.validate_template(TemplateBody=t_json)

# create or delete stack with:
# cfn.create_stack(**stack_args)
# cfn.delete_stack(StackName=stack_args['StackName'])