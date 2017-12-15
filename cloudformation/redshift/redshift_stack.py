import boto3
from awacs import s3
from awacs.aws import Statement, Allow, Policy, Action, Principal
from troposphere import Template, Ref, Parameter, iam, redshift, ec2, GetAtt
from awacs.sts import AssumeRole
import ruamel_yaml as yaml
from pkg_resources import resource_string
cfg = yaml.load(resource_string('cloudformation', 'config.yml'))

template = Template()
template.add_description('Redshift single-node stack')

STACK_NAME = 'Redshift-Stack-staging'

# --- Iam --- #

# TODO
redshift_bucket_param = template.add_parameter(
    Parameter(
        'BucketArn',
        Type='String',
        Description='S3 Bucket to store cluster outputs',
    ))


redshift_policy = iam.Policy(
    PolicyName='GrantRedshift',
    PolicyDocument={
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "redshift:*",
                    "iam:PassRole"
                ],
                "Resource": "*",
            }
        ]
    })

s3_policies = iam.Policy(
    PolicyName='S3Policies',
    PolicyDocument= Policy(
        Statement=[
            Statement(
                Sid='S3Access',
                Effect=Allow,
                Action=[
                    Action('s3', 'List*'),
                    Action('s3', 'Get*'),
                ],
                Resource=['*']
            ),
            Statement(
                Sid='S3WriteAccess',
                Effect=Allow,
                Action=[s3.DeleteObject,
                    s3.PutObject,
                    s3.GetBucketPolicy,
                    s3.ListMultipartUploadParts,
                    s3.AbortMultipartUpload,
                    ],
                Resource=[Ref(redshift_bucket_param)]
            )
        ]
    )
)

iam_role = template.add_resource(
    iam.Role(
        'RedshiftIAMRole',
        RoleName="RedshiftIAMRole",
        AssumeRolePolicyDocument=Policy(
            Statement=[
                Statement(
                    Effect=Allow,
                    Action=[AssumeRole],
                    Principal=Principal("Service", ["redshift.amazonaws.com"])
                )
            ]
        ),
        Policies=[s3_policies, redshift_policy]
    )
)

# --- clusters -- #

single_node_cluster = template.add_resource(
    redshift.Cluster(
        'Cluster',
        DependsOn='RedshiftIAMRole',
        DBName = "dwh",
        MasterUsername = 'franzi',
        MasterUserPassword = 'Yo!Something1',
        ClusterType="single-node",
        NodeType="dc2.large",
        IamRoles=[GetAtt(iam_role, 'Arn')],
        #AvailabilityZone="eu-west-1a", takes defaults, client connection needs security groups set, for now added new rule manually with myIp as source TODO !
        #VpcSecurityGroupIds=['vpc-.....'],
        #ClusterSubnetGroupName=cf['SUBNET_WEST_1A']
    )
)



template_json = template.to_json(indent=4)
print(template_json)

cfn = boto3.client('cloudformation')
cfn.validate_template(TemplateBody=template_json)
stack ={}
stack['StackName'] = STACK_NAME
stack['TemplateBody'] = template_json
stack['Capabilities'] =  ['CAPABILITY_NAMED_IAM']
stack['Parameters'] = [ {'ParameterKey': 'BucketArn', 'ParameterValue': cfg['redshift']['BUCKET_ARN']}]

# create or delete stack with:
#cfn.create_stack(**stack)
#cfn.delete_stack(StackName=stack['StackName'])

# test with client: select * from information_schema.tables;
