import boto3
import botocore
import random
import string
import json
import re
from troposphere import Ref, Template, Sub, Output, GetAtt
from troposphere.s3 import Bucket, Private
from troposphere.iam import PolicyType, User, AccessKey

clientname = input("Enter Client Name > ").lower()
stackname = input('Enter StackName > ').lower()

def main():
    create_stack()
    Output = get_outputs()

    print(Output)


def cfn_client():
    'Boto3 CloudFormation Client'
    cfn = boto3.client('cloudformation')
    return cfn



t = Template()

t.set_description(
    "AWS CloudFormation Template: This template creates two users"
    " and assigns various permissions for accessing an S3 bucket to them"
)

s3bucket = t.add_resource(Bucket('S3Bucket', BucketName=f'{clientname}-static-{"".join(random.choice(string.digits+string.ascii_lowercase) for i in range(6))}', AccessControl=Private,))

s3policy = t.add_resource(PolicyType('S3ReadPolicy', PolicyName='S3ReadPolicy', PolicyDocument={
    # This creates the S3 Bucket Read and List only Policy for the specified number of users
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
    # This creates the S3 Bucket Read and List only Policy for the specified number of users
    "Statement": [
        {
          "Action": "s3:PutObject",
          "Effect": "Allow",
          "Resource": Sub("arn:aws:s3:::${S3Bucket}/*")
        }
      ]
},
                                           Users=[Ref('RwUser')]))

ro_user = t.add_resource(User('RoUser', UserName=f'{clientname}-s3-ro')) # Read-Only User Creation
ro_key = t.add_resource(AccessKey('RoKey', UserName=Ref(ro_user))) # Read-Only AccessKey Creation
rw_user = t.add_resource(User('RwUser', UserName=f'{clientname}-s3-rw')) # Read-Write User Creation
rw_key = t.add_resource(AccessKey('RwKey', UserName=Ref(rw_user))) # Read-Write AccessKey Creation

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

template = t.to_yaml()

def create_stack(stack_name=stackname, cfn_template=template):
    params = {
        'StackName': stack_name,
        'TemplateBody': cfn_template,
        'Capabilities': ['CAPABILITY_NAMED_IAM']
    }

    try:
        response = cfn_client().create_stack(**params)
        waiter = cfn_client().get_waiter('stack_create_complete')
        waiter.wait(StackName=stack_name)  # Delays the execution of the get_output function
    except botocore.exceptions.ClientError as ex:
        error_message = ex.response['Error']['Message']
        print(error_message)

def _to_env(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).upper()


def get_outputs(stack=stackname):
    r = cfn_client().describe_stacks(StackName=stack)
    stack, = r['Stacks']
    outputs = stack['Outputs']

    out = {}
    for o in outputs:
        key = _to_env(o['OutputKey'])
        out[key] = o['OutputValue']
    return json.dumps(out, indent=2)


if __name__ == '__main__':
  main()




