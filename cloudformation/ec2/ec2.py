import ruamel_yaml as yaml
from pkg_resources import resource_string
from troposphere import Template, Parameter, ec2, Ref, Output
cfg = yaml.load(resource_string('cloudformation', 'config.yml'))

# --- template --- #
template = Template()
template.add_description('Simple EC2 stack')

# params
key_name_param = template.add_parameter(
    Parameter(
        'KeyName',
        Type='String',
        Description='AWS key name to ssh, pem file',
    )
)


mySecurityGroup = template.add_resource(
    ec2.SecurityGroup(
        'simpleSg',
        GroupDescription='Simple Security Group: Enable SSH access via port 22',
        SecurityGroupIngress=[ ec2.SecurityGroupRule( IpProtocol='tcp',
                                                      FromPort='22',
                                                      ToPort='22',
                                                      CidrIp='0.0.0.0/0')
        ]
    )
)

ec2_instance = template.add_resource(ec2.Instance(
    'Ec2Instance',
    ImageId='ami-e5083683',
    InstanceType='t2.micro',
    SecurityGroups=[Ref(mySecurityGroup)],
    Tags=[{'Key' : 'Name', 'Value' : 'SimpleEC2Instance'}],
    KeyName=Ref(key_name_param)
))

# for cross reference
template.add_output([
    Output('EC2Instance',
           Description='EC2',
           Value=Ref(ec2_instance))])

template.add_output([
    Output('securityGroup',
           Description='securityGroup',
           Value=Ref(mySecurityGroup))])

# Stack validation, creation and deletion
import boto3
template_json = template.to_json(indent=4)
print(template_json)

cfn = boto3.client('cloudformation')
cfn.validate_template(TemplateBody=template_json)
stack ={}
stack['StackName'] = 'SimpleEC2Stack'
stack['TemplateBody'] = template_json
stack['Parameters'] = [{ 'ParameterKey': 'KeyName', 'ParameterValue': cfg['KEY_NAME'] }]

# create or delete stack with:
#cfn.create_stack(**stack)
#cfn.delete_stack(StackName=stack['StackName'])

