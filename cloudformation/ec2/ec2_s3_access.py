from troposphere import Template, iam, Ref, Parameter, ec2
from awacs.aws import Allow, Policy, Principal, Statement, Action
from awacs.sts import AssumeRole
import ruamel_yaml as yaml
from pkg_resources import resource_string

cfg = yaml.load(resource_string('cloudformation', 'config.yml'))



t = Template()
t.add_description('EC2 instance with s3 read access')


# params
key_name_param = t.add_parameter(
    Parameter(
        'KeyName',
        Type='String',
        Description='AWS key name to ssh, pem file',
    )
)

policy = iam.Policy(
    PolicyName='S3ReadPolicy',
    PolicyDocument= Policy(
        Statement=[
            Statement(
                Sid='S3Access',
                Effect=Allow,
                Action=[
                    Action('s3', 'List*'),
                    Action('s3', 'Get*'),
                ],
                Resource=['arn:aws:s3:::*']
            )
        ]
    )
)


S3role = t.add_resource(iam.Role(
    'S3Role',
    RoleName="S3role",
    AssumeRolePolicyDocument=Policy(
        Statement=[
            Statement(
                Effect=Allow,
                Action=[AssumeRole],
                Principal=Principal("Service", ["ec2.amazonaws.com"])
            )
        ]
    ),
    Policies=[policy]
))

instance_profile = t.add_resource(iam.InstanceProfile("InstanceProfile", Roles=[Ref(S3role)]))

mySecurityGroup = ec2.SecurityGroup('simpleSG')
mySecurityGroup.GroupDescription = 'shh traffic allowed'
mySecurityGroup.SecurityGroupIngress = [ec2.SecurityGroupRule(IpProtocol='tcp',
                                                              FromPort='22',
                                                              ToPort='22',
                                                              CidrIp='0.0.0.0/0') # from everywhere
                                        ]
t.add_resource(mySecurityGroup)


my_instance = ec2.Instance('EC2InstanceWithS3Access')
my_instance.IamInstanceProfile = Ref(instance_profile)
my_instance.SecurityGroups = [Ref(mySecurityGroup)]
my_instance.ImageId = 'ami-e5083683'
my_instance.InstanceType = 't2.micro'
my_instance.Tags = [{"Key" : "Name", "Value" : "EC2WithS3Access"}]
my_instance.KeyName = Ref(key_name_param)
t.add_resource(my_instance)


import boto3
template_json = t.to_json(indent=4)
print(template_json)
cfn = boto3.client('cloudformation')
cfn.validate_template(TemplateBody=template_json)

stack ={}
stack['StackName'] = 'EC2WithS3AccessStack'
stack['TemplateBody'] = template_json
stack['Capabilities'] = ['CAPABILITY_NAMED_IAM']
stack['Parameters'] = [{ 'ParameterKey': 'KeyName', 'ParameterValue': cfg['KEY_NAME'] }]

#cfn.create_stack(**stack)
#cfn.delete_stack(StackName=stack['StackName'])


