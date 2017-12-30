import boto3
from awacs import s3
from awacs.aws import Statement, Allow, Policy, Action
from troposphere import Template, Ref, Parameter, iam, emr, ec2, GetAtt
import ruamel_yaml as yaml
from pkg_resources import resource_string
from troposphere.constants import M3_XLARGE
cfg = yaml.load(resource_string('cloudformation', 'config.yml'))

template = Template()
template.add_description('EMR stack with steps')

STACK_NAME = 'EMRWithStepsStack'
BOOTSTRAP_PATH = 's3://franziska-adler-deployments/production/aws_playground/cloudformation/emr/scripts/bootstrap_task_conda.sh'

### --- Iam --- ###

emr_write_bucket_param = template.add_parameter(
    Parameter(
        'WriteBucketArn',
        Type='String',
        Description='S3 Bucket Arn to store cluster outputs',
    ))

s3_policy_doc = Policy(
    Statement=[
        Statement(
            Sid='S3ReadAccess',
            Effect=Allow,
            Action=[Action("s3", "List*"),
                    Action("s3", "Get*")
                    ],
            Resource=[s3.ARN("*")]
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
            Resource=[Ref(emr_write_bucket_param)]
        )
    ]
)

emr_cluster_policy = Policy(
    Statement=[
        Statement(
            Sid='ClusterAccess',
            Effect=Allow,
            Action=[Action("elasticmapreduce", "List*"),
                    Action("elasticmapreduce", "AddJobFlowSteps")
                    ],
            Resource=["*"]#TODO restrict
        )
    ]
)


emr_service_role = template.add_resource(
    iam.Role(
        'EMRServiceRole',
        AssumeRolePolicyDocument={
            'Statement': [{
                'Effect': 'Allow',
                'Principal': {
                    'Service': [
                        'elasticmapreduce.amazonaws.com'
                    ]
                },
                'Action': ['sts:AssumeRole']
            }]
        },
        ManagedPolicyArns=[
            'arn:aws:iam::aws:policy/service-role/AmazonElasticMapReduceRole'
        ]
    )
)

emr_job_flow_role = template.add_resource(
    iam.Role(
        'EMRJobFlowRole',
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
        Policies=[
            iam.Policy(
                PolicyName='{}-S3Policy'.format(STACK_NAME),
                PolicyDocument=s3_policy_doc,
            ),
            iam.Policy(
                PolicyName='{}-ClusterAccessPolicy'.format(STACK_NAME),
                PolicyDocument=emr_cluster_policy,
            )
        ]
    )
)

emr_instance_profile = template.add_resource(
    iam.InstanceProfile(
        'EMRInstanceProfile',
        Roles=[Ref(emr_job_flow_role)],
    )
)

### --- Cluster --- ###

key_pair_name_param = template.add_parameter(
    Parameter(
        'KeyName',
        Type='String',
        Description='Key pair name to ssh',
    )
)

instance_count_param = template.add_parameter(
    Parameter(
        'InstanceCount',
        Type='Number',
        Description='Number of core instances',
        MaxValue='16'
    )
)

subnet_id_param = template.add_parameter(
    Parameter(
        'SubnetId',
        Type='String',
        Description='Subnet Id'
    )
)

mySecurityGroup = template.add_resource(
    ec2.SecurityGroup(
        'simpleSg',
        GroupDescription='Simple Security Group: Enable SSH access via port 22',
        SecurityGroupIngress=[ec2.SecurityGroupRule( IpProtocol='tcp',
                                                      FromPort='22',
                                                      ToPort='22',
                                                      CidrIp='0.0.0.0/0')
        ]
    )
)


cluster = template.add_resource(
    emr.Cluster(
        'Cluster',
        DependsOn=['simpleSg'],
        Name= 'ClusterWithSparkAndSteps',
        ReleaseLabel='emr-5.11.0',
        JobFlowRole=Ref(emr_instance_profile),
        ServiceRole=Ref(emr_service_role ),
        Instances=emr.JobFlowInstancesConfig(
            Ec2KeyName=Ref(key_pair_name_param),
            Ec2SubnetId=Ref(subnet_id_param),
            AdditionalMasterSecurityGroups=[GetAtt('simpleSg', 'GroupId')],
            AdditionalSlaveSecurityGroups = [GetAtt('simpleSg', 'GroupId')],
            MasterInstanceGroup=emr.InstanceGroupConfigProperty(
                Name='Master Instance',
                InstanceCount='1',
                InstanceType=M3_XLARGE,
                Market='ON_DEMAND'
            ),
            CoreInstanceGroup=emr.InstanceGroupConfigProperty(
                Name='Core Instance',
                InstanceCount=Ref(instance_count_param),
                InstanceType=M3_XLARGE,
                Market='SPOT',
                BidPrice='0.19'
            ),
        ),
        Applications=[
            emr.Application(Name='Hadoop'),
            emr.Application(Name='Spark'),
            emr.Application(Name='Ganglia')
        ],
        LogUri='s3://franziska-adler-emr/logs/',
        BootstrapActions=[
            emr.BootstrapActionConfig(
                Name='Add spark task and set conda',
                ScriptBootstrapAction=emr.ScriptBootstrapActionConfig(
                    Path=BOOTSTRAP_PATH,
                    Args=[cfg['emr']['SPARK_TASK_PATH']]
                )
            )
        ],
        Configurations=[
            emr.Configuration(
                Classification='spark-env',
                Configurations=[
                    emr.Configuration(
                        Classification="export",
                        ConfigurationProperties={
                            "SPARK_HOME": "/usr/lib/spark",
                            "PYSPARK_PYTHON": "/home/hadoop/conda/bin/python3.6",
                            "PYTHONHASHSEED": "123"
                        },
                    ),
                ]
            ),
            emr.Configuration(
                Classification="spark-defaults",
                ConfigurationProperties={
                    "spark.yarn.appMasterEnv.PYTHONHASHSEED": "123"
                }
            ),
            emr.Configuration(
                Classification="hadoop-env",
                Configurations=[
                    emr.Configuration(
                        Classification="export",
                        ConfigurationProperties={
                            "PYTHONHASHSEED": "123"
                        }
                    )
                ]
            )
        ]
    )
)


template_json = template.to_json(indent=4)
print(template_json)

cfn = boto3.client('cloudformation')
cfn.validate_template(TemplateBody=template_json)
stack ={}
stack['StackName'] = STACK_NAME
stack['TemplateBody'] = template_json
stack['Capabilities'] = ['CAPABILITY_IAM']
stack['Parameters'] = [ {'ParameterKey': 'KeyName', 'ParameterValue': cfg['KEY_NAME']},
                        {'ParameterKey': 'InstanceCount', 'ParameterValue': cfg['emr']['INSTANCE_COUNT']},
                        {'ParameterKey': 'WriteBucketArn', 'ParameterValue': cfg['emr']['WRITE_BUCKET_ARN']},
                        {'ParameterKey': 'SubnetId', 'ParameterValue': cfg['SUBNET_WEST_1B']}
                       ]

# create or delete stack with:
cfn.create_stack(**stack)
# cfn.delete_stack(StackName=stack['StackName'])

# execute spark app in test.py with
# /usr/lib/spark/bin/spark-submit test.py
#    spark-home/