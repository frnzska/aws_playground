from troposphere import Ref, iam, awslambda, GetAtt, logs, Parameter
from troposphere import Template
from awacs.aws import Statement, Action, Allow
from troposphere.cloudformation import CustomResource
import boto3
import ruamel_yaml as yaml
from pkg_resources import resource_string
cfg = yaml.load(resource_string('cloudformation', 'config.yml'))

STACK_NAME = cfg['log_s3events_2_cloudwatch_lambda']['STACK_NAME']
WATCH_BUCKET = cfg['log_s3events_2_cloudwatch_lambda']['WATCH_BUCKET']
watch_bucket_arn = '{arn:aws:s3:::{WB}'.format(WB=WATCH_BUCKET)

template = Template()
description = 'Bucket monitoring'
template.add_description(description)

# AWSTemplateFormatVersion
template.add_version('2010-09-09')

# params

bucket_arn_param = template.add_parameter(
    Parameter(
        'WatchBucketArn',
        Type='String',
        Description='Bucket arn of bucket to be logged'
    )
)

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
            PolicyName='cfnDescribeStacks',
            PolicyDocument={
                "Version": "2012-10-17",
                "Statement": [
                    Statement(
                        Sid='cfnDescribe',
                        Effect=Allow,
                        Action=[
                            Action('cloudformation', 'DescribeStacks'),
                            Action('cloudformation', 'DescribeStackResources'),
                        ],
                        Resource=["*"]
                    ),
                ]
            }
        )
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
    ))

lambda_fct = template.add_resource(
    awslambda.Function(
        'S3Logging',
        FunctionName=cfg['log_s3events_2_cloudwatch_lambda']['FCT'],
        Description='Log bucket events',
        Handler='lambda_function.lambda_handler',
        Role=GetAtt('LambdaExecutionRole', 'Arn'),
        Code=awslambda.Code(
            S3Bucket=cfg['log_s3events_2_cloudwatch_lambda']['DEPLOYMENT_BUCKET'],
            S3Key=cfg['log_s3events_2_cloudwatch_lambda']['S3_KEY'],
        ),
        Runtime='python3.6',
        Timeout='30',
        MemorySize=128,
        Environment = awslambda.Environment('LambdaVars', Variables={'STACK_NAME': STACK_NAME})
    )
)

template.add_resource(
    awslambda.Permission(
       'lambdas3execute',
        Principal="s3.amazonaws.com",
        Action='lambda:InvokeFunction',
        FunctionName=GetAtt('S3Logging', 'Arn'),
        SourceArn=Ref(bucket_arn_param)
    )
)

# invoke function once at built
template.add_resource(
    CustomResource(
        'functionInvocation',
        ServiceToken=GetAtt('S3Logging', 'Arn'),
    )
)




t_json = template.to_json(indent=4)

# ----- Stack Args ----- #

stack_args = {
    'StackName': STACK_NAME,
    'TemplateBody': template.to_json(indent=4),
    'Parameters': [
       { 'ParameterKey': 'WatchBucketArn', 'ParameterValue': watch_bucket_arn }
    ],
    'Tags': [ { 'Key': 'Stage', 'Value': 'staging'}],
    'Capabilities': ['CAPABILITY_IAM',],
}

cfn = boto3.client('cloudformation')
print(t_json)
cfn.validate_template(TemplateBody=t_json)


def add_bucket_notification_on_s3_event(*, bucket, lambda_function, event):
    """Add bucket notificatoin lambda to bucket
    Parameters
    ----------
    bucket: str
        name of the bucket
    lambda_function: str
        name of the lambda function to be executed with events
    event: str
        s3 event triggering the lambda function 

    """
    s3_client = boto3.client('s3')
    lambda_client = boto3.client('lambda')
    lambda_arn = lambda_client.get_function_configuration(FunctionName=cfg['log_s3events_2_cloudwatch_lambda']['FCT'])['FunctionArn']
    notification_config = {
        'LambdaFunctionConfigurations': [
            {
                'LambdaFunctionArn': lambda_arn,
                'Events': [
                    event
                ],
            },
        ]

    }
    s3_client.put_bucket_notification_configuration(Bucket=bucket, NotificationConfiguration=notification_config)

# Step 1: Create stack
# cfn.create_stack(**stack_args)
# cfn.delete_stack(StackName=stack_args['StackName'])

# Step 2: Enable Bucket Notification on eventype, done once
# add_bucket_notification_on_s3_event(bucket= WATCH_BUCKET, lambda_function=lambda_fct , event='s3:ObjectCreated:Put')