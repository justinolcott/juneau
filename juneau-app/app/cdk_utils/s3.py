import boto3
from botocore.exceptions import ClientError
from aws_cdk import core
import aws_cdk.aws_s3 as s3


class MyS3Stack(core.Stack):
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        bucket_name = 'my-unique-bucket-name'

        # Check if the bucket exists
        if not check_if_bucket_exists(bucket_name):
            # If the bucket doesn't exist, create it
            s3.Bucket(self, 
                      "MyBucket", 
                      bucket_name=bucket_name, 
                      removal_policy=core.RemovalPolicy.DESTROY)
            
    def check_if_bucket_exists(self, bucket_name):
        s3_client = boto3.client('s3')
        try:
            # Try to get the bucket's metadata to check if it exists
            s3_client.head_bucket(Bucket=bucket_name)
            return True
        except ClientError as e:
            # If the error is "Not Found", the bucket doesn't exist
            if e.response['Error']['Code'] == 'NotFound':
                return False
            else:
                raise e  # Raise any other errors

    def upload_to_bucket(self, bucket_name):
        # Check if the bucket exists
            if not self.check_if_bucket_exists(bucket_name):
                # If the bucket doesn't exist, create it
                s3.Bucket(self, 
                        "MyBucket", 
                        bucket_name=bucket_name, 
                        removal_policy=core.RemovalPolicy.DESTROY)