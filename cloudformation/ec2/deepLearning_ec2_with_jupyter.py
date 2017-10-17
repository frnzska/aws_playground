from troposphere import ec2, Ref, Template, iam, Parameter, Base64, Join, FindInMap, Output, GetAtt
import boto3
from awacs import s3
from awacs.aws import Statement, Allow, Action, Policy, Principal
from awacs.sts import AssumeRole
import ruamel_yaml as yaml
from pkg_resources import resource_string
cfg = yaml.load(resource_string('cloudformation', 'config.yml'))

SUBNET_WEST_1A = cfg['SUBNET_WEST_1A']
SUBNET_WEST_1B = cfg['SUBNET_WEST_1B']
SUBNET_WEST_1C = cfg['SUBNET_WEST_1C']

S3_KEY_JUPYTER_CONF = cfg['deepLearning_ec2']['S3_KEY_JUPYTER_CONF']
S3_KEY_INSTALL = cfg['deepLearning_ec2']['S3_KEY_INSTALL']

sep= '-'
STACK_NAME = sep.join(['Jupyter', cfg['deepLearning_ec2']['EC2_STACK_NAME'], cfg['deepLearning_ec2']['STAGE']])

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
    AssumeRolePolicyDocument=Policy(
        Statement=[
            Statement(
                Effect=Allow,
                Action=[AssumeRole],
                Principal=Principal("Service", ["ec2.amazonaws.com"])
            )
        ]
    ),
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
        SecurityGroupIngress=[ec2.SecurityGroupRule(IpProtocol='tcp',
                                                    FromPort='22',
                                                    ToPort='22',
                                                    CidrIp='0.0.0.0/0')
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
                          'cd /home/ec2-user \n',
                          'mkdir -p /mnt/jupyter-notebooks \n',
                          'chmod 777 /mnt/jupyter-notebooks \n',
                          'su ec2-user -c "aws s3 cp ', S3_KEY_JUPYTER_CONF, ' /home/ec2-user/.jupyter/jupyter_notebook_config.py" \n',
                          'su ec2-user -c "aws s3 cp ', S3_KEY_INSTALL, ' /home/ec2-user/certificate_and_s3fuse.sh" \n',
                          'sh /home/ec2-user/certificate_and_s3fuse.sh  \n',
                          'cd /mnt/jupyter-notebooks \n',
                          'su ec2-user -c "jupyter notebook" \n',
                          '\n'
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
# cfn.create_stack(**stack)
# cfn.delete_stack(StackName=stack['StackName'])

### set the connection with:
# ssh -i ~/mykeypair.pem -L 8157:127.0.0.1:8888 ec2-user@ec2-###-##-##-###.compute-1.amazonaws.com (public dns)
# available https://127.0.0.1:8157