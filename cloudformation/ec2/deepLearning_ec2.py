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
