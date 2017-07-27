from troposphere import Template, iam, Base64, Join, ec2, Ref, Parameter
import ruamel_yaml as yaml
from pkg_resources import resource_string

cfg = yaml.load(resource_string('cloudformation', 'config.yml'))

t = Template()
t.add_description('EC2 instance with cloudwatch log agent installed. Logs var/log/messages of instance to cloudwatch')

# params
key_name_param = t.add_parameter(
    Parameter(
        'KeyName',
        Type='String',
        Description='AWS key name to ssh, pem file',
    )
)

logconfig_on_s3_param = t.add_parameter(
    Parameter(
        'LogConfig',
        Type='String',
        Description='s3 location with log config stored',
    )
)

pol_doc = {
    'Statement': [{
        'Sid': 'S3ReadAccess',
        'Effect': 'Allow',
        'Action': [ 's3:List*', 's3:Get*'],
        'Resource': ['arn:aws:s3:::*']
        },
        {
        'Effect': 'Allow',
        'Action': [
            'logs:CreateLogGroup',
            'logs:CreateLogStream',
            'logs:PutLogEvents',
            'logs:DescribeLogStreams'
            ],
        'Resource': ['arn:aws:logs:*:*:*']
        }
    ]
}

policy = iam.Policy(
    "myReadPolicy",
    PolicyName="ReadS3AndLog",
    PolicyDocument=pol_doc
)

accessRole = t.add_resource(iam.Role(
    "ec2accessS3role",
    AssumeRolePolicyDocument={
        'Statement': [{
            'Effect': 'Allow',
            'Principal': {
                'Service': ['ec2.amazonaws.com']
                },
            'Action': ['sts:AssumeRole']
        }]
    },
    Policies=[policy]
))

cfninstanceprofile = t.add_resource(iam.InstanceProfile(
    "CFNInstanceProfile",
    Roles=[Ref(accessRole)]
))


ec2_instance = ec2.Instance("EC2WithCloudwatchLogsAgent")
ec2_instance.ImageId="ami-e5083683"
ec2_instance.InstanceType="t2.micro"
mySecurityGroup = t.add_resource(
    ec2.SecurityGroup(
        'simpleSg',
        GroupDescription='Simple Security Group: Enable SSH access via port 22',
        SecurityGroupIngress=[
            {
                'IpProtocol': 'tcp',
                'CidrIp': '0.0.0.0/0',
                'FromPort': '22',
                'ToPort': '22'
            }
        ]
    )
)

ec2_instance.SecurityGroups=[Ref(mySecurityGroup)]
ec2_instance.Tags=[{"Key" : "Name", "Value" : "EC2withCloudwatch"}]
ec2_instance.KeyName=Ref(key_name_param)
ec2_instance.IamInstanceProfile=Ref(cfninstanceprofile)

# add logs agent
ec2_instance.UserData = Base64(
            Join(
                '',
                ['#!/bin/bash \n',
                 'sudo yum update -y \n',
                 'curl https://s3.amazonaws.com/aws-cloudwatch/downloads/latest/awslogs-agent-setup.py -O \n',
                 'chmod +x awslogs-agent-setup.py \n',
                 './awslogs-agent-setup.py -n -r eu-west-1 -c', Ref(logconfig_on_s3_param), '\n',
                 ])
        )


t.add_resource(ec2_instance)



#### -- add metric filter -- ####

from troposphere import logs

metric_transformation = logs.MetricTransformation("TestMetricTransformation")
metric_transformation.MetricName = "myTestMetric"
metric_transformation.MetricNamespace = "EC2Logfiles" # not to use AWS/... reserved for Aws
metric_transformation.MetricValue = "1"

metric_filter = logs.MetricFilter('myTestMetricFilter')
metric_filter.FilterPattern = "[month, day, time, ip, action=yum*, ...]"
metric_filter.LogGroupName = "ec2logs/var/log/messages"
metric_filter.MetricTransformations = [metric_transformation]

t.add_resource(metric_filter)


import boto3
template_json = t.to_json(indent=4)
print(template_json)
cfn = boto3.client('cloudformation')
cfn.validate_template(TemplateBody=template_json)



stack ={}
stack['StackName'] = 'EC2WithCloudwatch'
stack['TemplateBody'] = template_json
stack['Capabilities'] = ['CAPABILITY_IAM']
stack['Parameters'] = [{ 'ParameterKey': 'KeyName', 'ParameterValue': cfg['KEY_NAME']},
                       { 'ParameterKey': 'LogConfig', 'ParameterValue': cfg['ec2_with_cloudwatch_agent']['LOG_CONFIG']}]

#cfn.create_stack(**stack)
#cfn.delete_stack(StackName=stack['StackName'])
