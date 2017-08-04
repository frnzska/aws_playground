"""Creates Bucket with event notification and sns subscription on event upload"""
import boto3
from troposphere import Template, sns, Ref, s3, Parameter

myEmail = 'EmailAddress'
bucketName = 'someBucketName'

template = Template()
template.add_description('Test SNS')

subscriber_mail_param = template.add_parameter(
    Parameter(
        'SubscriptionEmail',
        Type='String',
        Description='Email of subscriber',
    )
)

event_bucket_param = template.add_parameter(
    Parameter(
        'EventBucketName',
        Type='String',
        Description='Name of bucket which fires event',
    )
)


# allow s3 to publish to sns
s3_policy_doc = {
    'Statement': [{
        'Sid': 'S3BucketNotification',
        'Effect': 'Allow',
        'Principal': {
                    'Service': [
                        's3.amazonaws.com'
                    ]
                },
        'Action':['sns:Publish'],
        'Resource': "*"
    }]
}

# 1. topic
topic = sns.Topic('snstopic')
topic.DisplayName = 'myS3SNSTopic'
topic.TopicName='myS3SNSTopic'
template.add_resource(topic)

# 2. topic policy
template.add_resource(
    sns.TopicPolicy(
        'snsTitle',
        PolicyDocument= s3_policy_doc,
        Topics=[Ref(topic)],
    )
)

# 3. subscription
subscription = sns.SubscriptionResource(
        'snsSubscription',
        Endpoint=Ref(subscriber_mail_param),
        Protocol='email',
        TopicArn=Ref(topic),
    )
template.add_resource(subscription)

# 4. Bucket with SNS Event Notification
template.add_resource(
    s3.Bucket(
        'mySNSBucket',
        BucketName=Ref(event_bucket_param),
        NotificationConfiguration=s3.NotificationConfiguration(
            TopicConfigurations= [s3.TopicConfigurations(
                Event= "s3:ObjectCreated:Put",
                Topic= Ref(topic),
            )]
        )
    )
)


template_json = template.to_json(indent=4)
print(template_json)
cfn = boto3.client('cloudformation')
cfn.validate_template(TemplateBody=template_json)

stack ={}
stack['StackName'] = 'S3WithSNS-development'
stack['TemplateBody'] = template_json
stack['Capabilities'] = ['CAPABILITY_IAM']
stack['Parameters'] = [
                        {'ParameterKey': 'SubscriptionEmail',
                         'ParameterValue': myEmail},
                        {'ParameterKey': 'EventBucketName',
                         'ParameterValue': bucketName}
                      ]


#cfn.create_stack(**stack)
#cfn.delete_stack(StackName=stack['StackName'])