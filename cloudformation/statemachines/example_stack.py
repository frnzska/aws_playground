from troposphere import Ref, iam, awslambda, GetAtt, logs, Parameter
from troposphere import Template
from awacs.aws import Statement, Action, Allow
from troposphere.cloudformation import CustomResource
import boto3
import ruamel_yaml as yaml
from pkg_resources import resource_string




cfg = yaml.load(resource_string('statemachine_example', 'config.yml'))

STACK_NAME = cfg['statemachine_example']['STACK_NAME']


template = Template()
description = 'Template for first state machine'
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
                    "Service": ["states.eu-west-1.amazonaws.com"], #check if correct, parametrize later
                }
            }]
        },

))


### Lambda fct ###

### state machine ###