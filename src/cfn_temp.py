import boto3
import random
import string
from troposphere import Ref, Template, Sub, Output, GetAtt
from troposphere.s3 import Bucket, Private
from troposphere.iam import PolicyType, User, AccessKey

cf = boto3.client('cloudformation')
clientname = input("Enter Client Name > ").lower()


t = Template()

t.set_description(
    "AWS CloudFormation Template: This template creates two users"
    " and assigns various permissions for accessing an S3 bucket to them"
)

s3bucket = t.add_resource(Bucket('S3Bucket', BucketName=f'{clientname}-static-{"".join(random.choice(string.digits+string.ascii_lowercase) for i in range(6))}', AccessControl=Private,))

s3policy = t.add_resource(PolicyType('S3ReadPolicy', PolicyName='S3ReadPolicy', PolicyDocument={
    "Statement": [
        {
            "Action": "s3:GetObject",
            "Effect": "Allow",
            "Resource": Sub("arn:aws:s3:::${S3Bucket}/*")
        },
        {
            "Action": "s3:ListBucket",
            "Effect": "Allow",
            "Resource": Sub("arn:aws:s3:::${S3Bucket}")
        }
    ]
},
                                     Users=[Ref('RoUser'), Ref('RwUser')]))

s3write_policy = t.add_resource(PolicyType('S3WritePolicy', PolicyName='S3WritePolicy', PolicyDocument={
    "Statement": [
        {
          "Action": "s3:PutObject",
          "Effect": "Allow",
          "Resource": Sub("arn:aws:s3:::${S3Bucket}/*")
        }
      ]
},
                                           Users=[Ref('RwUser')]))

ro_user = t.add_resource(User('RoUser', UserName=f'{clientname}-s3-ro'))

ro_key = t.add_resource(AccessKey('RoKey', UserName=Ref(ro_user)))

rw_user = t.add_resource(User('RwUser', UserName=f'{clientname}-s3-rw'))

rw_key = t.add_resource(AccessKey('RwKey', UserName=Ref(rw_user)))



t.add_output(Output(
    "WebsiteURL",
    Value=GetAtt(s3bucket, "WebsiteURL"),
    Description='URL for website hosted on S3'
))

t.add_output(Output(
    "ReadOnlyAccessKey",
    Value=Ref(ro_key)
))

t.add_output(Output(
    "ReadOnlySecretKey",
    Value=GetAtt(ro_key, "SecretAccessKey")
))

t.add_output(Output(
    "ReadWriteAccessKey",
    Value=Ref(rw_key)
))

t.add_output(Output(
    "ReadWriteSecretKey",
    Value=GetAtt(rw_key, "SecretAccessKey")
))



cfn = t.to_yaml()

cf.create_stack(
    StackName=input('Enter StackName > ').lower(),
    TemplateBody=cfn,
    Capabilities=['CAPABILITY_NAMED_IAM']
)
