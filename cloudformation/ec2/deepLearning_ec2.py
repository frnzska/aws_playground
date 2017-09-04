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
