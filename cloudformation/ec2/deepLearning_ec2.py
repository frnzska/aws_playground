from troposphere import ec2, Ref, Template, iam, Parameter, Base64, Join, FindInMap, Output, GetAtt
import boto3
from awacs import s3
from awacs.aws import Statement, Allow, Action, Policy
import ruamel_yaml as yaml
from pkg_resources import resource_string
cfg = yaml.load(resource_string('cloudformation', 'config.yml'))

SUBNET_WEST_1A = cfg['SUBNET_WEST_1A']
SUBNET_WEST_1B = cfg['SUBNET_WEST_1B']
SUBNET_WEST_1C = cfg['SUBNET_WEST_1C']

sep= '-'
STACK_NAME = sep.join([cfg['deepLearning_ec2']['EC2_STACK_NAME'], cfg['deepLearning_ec2']['STAGE']])

t = Template()

# --- IAM ---

write_bucket_param = t.add_parameter(
    Parameter(
        'WriteBucket',
        Type='String',
        Description='S3 bucket to write to',
    )
)

s3_doc = Policy(
    Statement=[
        Statement(
            Sid='WriteS3',
            Effect=Allow,
            Action=[s3.DeleteObject,
                    s3.PutObject,
                    s3.GetBucketPolicy,
                    s3.ListMultipartUploadParts,
                    s3.AbortMultipartUpload,
                    ],
            Resource=[Ref(write_bucket_param)]
        ),
        Statement(
            Sid='ReadS3',
            Effect=Allow,
            Action=[Action("s3", "List*"),
                    Action("s3", "Get*")
                    ],
            Resource=['arn:aws:s3:::*']
        )
    ]
)

s3_access_policy = iam.Policy(
    "s3AccessPolicy",
    PolicyName= sep.join([cfg['deepLearning_ec2']['EC2_STACK_NAME'], 's3ReadPolicy']),
    PolicyDocument=s3_doc
)


s3_access_role = t.add_resource(iam.Role(
    "S3AccessRole",
    AssumeRolePolicyDocument={
        'Statement': [{
            'Effect': 'Allow',
            'Principal': {
                'Service': [
                    'ec2.amazonaws.com'
                ]
            },
            'Action': ['sts:AssumeRole']
        }]
    },
    Policies=[s3_access_policy]
))

# Output
t.add_output([
    Output('S3AccessRole',
           Value=Ref(s3_access_role),
           Description='EC2 instance profile role'
           )
    ]
)

# --- instance ---

t.add_mapping(
    'AZMap', {
        'eu-west-1a': {'SubnetId': SUBNET_WEST_1A},
        'eu-west-1b': {'SubnetId': SUBNET_WEST_1B},
        'eu-west-1c': {'SubnetId': SUBNET_WEST_1C},
    })

az_param = t.add_parameter(
    Parameter(
        'AZName',
        Type='String',
        Description='AvailabilityZone of the stack',
        AllowedValues=['eu-west-1a', 'eu-west-1b', 'eu-west-1c']
    ))

stage_param = t.add_parameter(
    Parameter(
        'Stage',
        Type='String',
        Description='Stage of this stack: staging or production',
        AllowedValues=['staging', 'production']
    ))

instance_type_param = t.add_parameter(
    Parameter(
        'InstanceType',
        Type='String',
        Description='Instance Type'
    ))


key_name_param = t.add_parameter(
    Parameter(
        'KeyName',
        Type='String',
        Description='Key Name',
    ))


SecurityGroup = t.add_resource(
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

instance_profile = t.add_resource(iam.InstanceProfile("InstanceProfile", Roles=[Ref(s3_access_role)]))


ec2_instance = t.add_resource(ec2.Instance(
    'Ec2Instance',
    ImageId = "ami-d36386aa",
    InstanceType = Ref(instance_type_param),
    SecurityGroupIds=[GetAtt('simpleSg', 'GroupId')],
    Tags=[{"Key" : "Name", "Value" : "deep_learning_EC2"}],
    KeyName=Ref(key_name_param),
    SubnetId=FindInMap('AZMap', Ref(az_param), 'SubnetId'),
    IamInstanceProfile=Ref(instance_profile),
    UserData = Base64(
                     Join(
                         '',
                         ['#!/bin/bash -xe\n',
                          'sudo easy_install3 pip \n',
                          'sudo pip install awscli',
                          '\n',
                          ])
               )
))


t.add_output([
    Output('AvailabilityZone',
           Value=GetAtt(ec2_instance, 'AvailabilityZone'),
           Description='AvailabilityZone of the EC2 instance'
           )
])




stack = {
    'StackName': STACK_NAME,
    'TemplateBody': t.to_json(indent=4),
    'Parameters': [
        {
            'ParameterKey': 'Stage',
            'ParameterValue': cfg['deepLearning_ec2']['STAGE'],
            'UsePreviousValue': False
        },
        {
            'ParameterKey': 'InstanceType',
            'ParameterValue': cfg['deepLearning_ec2']['INSTANCE_TYPE']
        },
        {
            'ParameterKey': 'AZName',
            'ParameterValue': cfg['deepLearning_ec2']['AZ_NAME']
        },
        {
            'ParameterKey': 'KeyName',
            'ParameterValue': cfg['KEY_NAME']
        },
        {
            'ParameterKey': 'WriteBucket',
            'ParameterValue': cfg['deepLearning_ec2']['WRITE_BUCKET_ARN']
        }
    ],
    'Tags': [
        {
            'Key': 'Stage',
            'Value': cfg['deepLearning_ec2']['STAGE']
        },
        {
            'Key': 'Purpose',
            'Value': 'DeepLearningEC2'
        }
    ],
    'Capabilities': [
        'CAPABILITY_IAM',
    ],
}


template_json = t.to_json(indent=4)
print(template_json)
cfn = boto3.client('cloudformation')
cfn.validate_template(TemplateBody=template_json)

# create or delete stack with:
#cfn.create_stack(**stack)
#cfn.delete_stack(StackName=stack['StackName'])


# ssh -A -t -t bastion ssh ec2-user@ip-10-100-170-110.eu-west-1.compute.internal