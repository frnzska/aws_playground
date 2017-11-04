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
lambda_fct = template.add_resource(
    awslambda.Function(
        'ExampleFct',
        FunctionName=cfg['statemachine_example']['FCT'],
        Description='Lambda for Statemachine',
        Handler='lambda_function.lambda_handler',
        Role=GetAtt('LambdaExecutionRole', 'Arn'),
        Code=awslambda.Code(
            S3Bucket=cfg['statemachine_example']['DEPLOYMENT_BUCKET'],
            S3Key=cfg['statemachine_example']['S3_KEY'],
        ),
        Runtime='python3.6',
        Timeout='30',
        MemorySize=128
    )
)

### state machine ###
resource = GetAtt('ExampleFct', 'Arn')
lambda_fct_arn = 'arn:aws:lambda:eu-west-1:369667221252:function:' + cfg['statemachine_example']['FCT']
definition_str = json.dumps({
  "StartAt": "A",
  "States": {
      "A": {
          "Type": "Task",
          "Resource": lambda_fct_arn,
          "ResultPath": "$.who",
          "Next": "B"
      },
    "B": {
      "Type": "Task",
      "Resource": lambda_fct_arn,
      "End": True
    }
  }
})

statemachine = template.add_resource(
    stepfunctions.StateMachine(
        'ExampleStateMachine',
        DependsOn= 'ExampleFct',
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
    'Capabilities': ['CAPABILITY_IAM',],
}

cfn = boto3.client('cloudformation')
print(t_json)
cfn.validate_template(TemplateBody=t_json)

# create or delete stack with:
# cfn.create_stack(**stack_args)
# cfn.delete_stack(StackName=stack_args['StackName'])

