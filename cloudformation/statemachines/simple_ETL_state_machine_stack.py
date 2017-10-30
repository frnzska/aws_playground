from troposphere import Ref, iam, awslambda, GetAtt, Base64, Join, stepfunctions, Sub
from troposphere import Template
from awacs.aws import Statement, Action, Allow
from troposphere.cloudformation import CustomResource
import boto3
import ruamel_yaml as yaml
from pkg_resources import resource_string
import json
import yaml



cfg = yaml.load(resource_string('cloudformation', 'config.yml'))

STACK_NAME = cfg['simple_ETL_state_machine']['STACK_NAME']
FUNCTION_NAME_1 = cfg['simple_ETL_state_machine']['FCT_1']
DEPLOYMENT_BUCKET = cfg['simple_ETL_state_machine']['DEPLOYMENT_BUCKET']
S3_KEY_1 = cfg['simple_ETL_state_machine']['S3_KEY_1']
#FUNCTION_NAME_2 = cfg['simple_ETL_state_machine']['FCT_2']

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
        FunctionName=FUNCTION_NAME_1,
        Description='Lambda 1 for Simple ETL Statemachine',
        Handler='validate.lambda',
        Role=GetAtt('LambdaExecutionRole', 'Arn'),
        Code=awslambda.Code(
            S3Bucket=DEPLOYMENT_BUCKET,
            S3Key=S3_KEY_1,
        ),
        Runtime='python3.6',
        Timeout='30',
        MemorySize=128
    )
)

### build stack

t_json = template.to_json(indent=4)

# ----- Stack Args ----- #

stack_args = {
    'StackName': STACK_NAME,
    'TemplateBody': template.to_json(indent=4),
    'Capabilities': ['CAPABILITY_IAM',],
}

cfn = boto3.client('cloudformation')
print(t_json)
cfn.validate_template(TemplateBody=t_json)

# create or delete stack with:
# cfn.create_stack(**stack_args)
# cfn.delete_stack(StackName=stack_args['StackName'])