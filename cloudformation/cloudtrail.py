from troposphere import Template, Ref, GetAtt
from troposphere.cloudtrail import Trail
from troposphere.iam import Policy, Role
from troposphere.logs import LogGroup
import boto3



STACK_NAME = 'CloudTrailStack'
LOG_GROUP_NAME = 'CloudTrail/S3Bucket'
LOG_BUCKET_NAME = 'cloudtrail-xyz-logs'

template = Template()
description = 'Bucket monitoring'
template.add_description(description)

template.add_version('2010-09-09')

log_group = template.add_resource(
    LogGroup(
        'LogGroup',
        LogGroupName=LOG_GROUP_NAME,
        RetentionInDays=7
    )
)

# grant Cloudtrail permission to write to Coudwatch logs and s3

log_stream_arn = '{PREFIX}:{LOG_GROUP_NAME}:{LOG_STREAM}'.format(PREFIX="arn:aws:logs:eu-west-1:369667221252:log-group",
                                                                LOG_GROUP_NAME=LOG_GROUP_NAME,
                                                                LOG_STREAM="log-stream:369667221252_CloudTrail_eu-west-1")
log_bucket_arn = '{PREFIX}{LOG_BUCKET_NAME}'.format(PREFIX='arn:aws:s3:::',
                                                    LOG_BUCKET_NAME=LOG_BUCKET_NAME)
log_bucket_folder_arn = '{PREFIX}{LOG_BUCKET_NAME}{FOLDER}'.format(PREFIX='arn:aws:s3:::',
                                                    LOG_BUCKET_NAME=LOG_BUCKET_NAME,
                                                    FOLDER='/AWSLogs/369667221252/*')
policy_document = {
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "CreateLogStream",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "logs:DescribeLogStreams"
      ],
      "Resource": [log_stream_arn]
    },
    {
      "Sid": "S3Access",
      "Effect": "Allow",
      "Action": [
          "s3:GetBucketAcl",

      ],
      "Resource": [log_bucket_arn]
    },
    {
      "Sid": "S3Write",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
      ],
      "Resource": [log_bucket_folder_arn]
    }
  ]
}


policy = Policy(PolicyName='logging', PolicyDocument=policy_document)
log_role = template.add_resource(
    Role(
        'logRole',
        AssumeRolePolicyDocument={
            'Statement': [{
                'Effect': 'Allow',
                'Principal': {
                    'Service': [
                        'cloudtrail.amazonaws.com'
                    ]
                },
                'Action': ['sts:AssumeRole']
            }]
        },
        Policies=[policy]
    )
)

trail = template.add_resource(
    Trail(
        'MyTrail',
        DependsOn=['LogGroup', 'logRole'],
        CloudWatchLogsLogGroupArn=GetAtt(log_group, "Arn"),
        CloudWatchLogsRoleArn=GetAtt(log_role, "Arn"),
        EnableLogFileValidation=True,
        IsLogging=True,
        S3BucketName= LOG_BUCKET_NAME, #bucket name for log files
    )
)

t_json = template.to_json(indent=4)


stack ={}
stack['StackName'] = STACK_NAME
stack['TemplateBody'] = t_json
stack['Capabilities'] = ['CAPABILITY_IAM']

cfn = boto3.client('cloudformation')
print(t_json)
cfn.validate_template(TemplateBody=t_json)

#cfn.create_stack(**stack)
cfn.delete_stack(StackName=stack['StackName'])
