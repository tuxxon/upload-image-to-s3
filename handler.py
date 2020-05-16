import boto3
import json
import logging
import os

from botocore.client import Config
from botocore.exceptions import ClientError
from urllib.parse import urlparse


CONTENT_FORMAT = """
<html>
  <head>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
  </head>
  <body>
    <!-- Copy the 'url' value returned by S3Client.generate_presigned_post() -->
    <form action="{action_url}" method="POST" enctype="multipart/form-data">
      <!-- Copy the 'fields' key:values returned by S3Client.generate_presigned_post() -->
      <input type="hidden" name="key" value="{key}" />
      <input type="hidden" name="x-amz-algorithm" value="AWS4-HMAC-SHA256" />
      <input type="hidden" name="x-amz-credential" value="{credential}" />
      <input type="hidden" name="x-amz-date" value="{date}" />
      <input type="hidden" name="policy" value="{policy}" />
      <input type="hidden" name="x-amz-signature" value="{signature}" />
    File:
      <input type="file"   name="file" /> <br />
      <input type="submit" name="submit" value="Upload to Amazon S3" />
    </form>
  </body>
</html>
    """

AccessKey = os.getenv('AccessKey')
SecretKey = os.getenv('SecretKey')

def create_presigned_post(
    bucket_name,
    key_name,
    fields=None,
    conditions=None,
    expiration=3600
):

    """Generate a presigned URL S3 POST request to upload a file

    :param bucket_name: string
    :param object_name: string
    :param fields: Dictionary of prefilled form fields
    :param conditions: List of conditions to include in the policy
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Dictionary with the following keys:
        url: URL to post to
        fields: Dictionary of form fields and values to submit with the POST
    :return: None if error.
    """

    # Generate a presigned S3 POST URL
    s3_client = boto3.client('s3',
        aws_access_key_id=AccessKey,
        aws_secret_access_key=SecretKey,
        region_name=os.getenv('Region'),
        config=Config(signature_version='s3v4')
    )
    try:

        response = s3_client.generate_presigned_post(
            bucket_name,
            key_name,
            Fields=None,
            Conditions=None,
            ExpiresIn=expiration
        )
    except ClientError as e:
        logging.error(e)
        return None

    # The response contains the presigned URL and required fields
    return response


def upload_image_to_s3(event, context):

    print("===> event = {}".format(event))

    #headers = event['headers']
    resourcePath = event['resource']
    httpMethod = event['httpMethod']
    querystring = event['queryStringParameters']

    resp = create_presigned_post(
        bucket_name = 'cf.stackcraft.co',
        key_name = querystring['name'],
        fields = {"acl":"private","Content-Type": "image/jpeg"},
        conditions = [
            {"acl":"private"},
            {"Content-Type": "image/jpeg"}
        ]
    )

    print("===> response = {}".format(resp))
    #print("===> url parse = {}".format(urlparse(resp)))

    fields = resp['fields']
    
    content_html = CONTENT_FORMAT.format(
        action_url = resp['url'],
        key = querystring['name'],
        credential = fields['x-amz-credential'],
        date = fields['x-amz-date'],
        policy = fields['policy'],
        signature = fields['x-amz-signature']
    )


    body = {
        "message": "Go Serverless v1.0! Your function executed successfully!",
        "input": event
    }

    headers = {}
    headers['Content-Type'] = 'text/html'
    response = {
        "statusCode": 200,
        "headers": headers,
        "body": content_html #json.dumps(body)
    }

    return response

    # Use this code if you don't use the http event with the LAMBDA-PROXY
    # integration
    """
    return {
        "message": "Go Serverless v1.0! Your function executed successfully!",
        "event": event
    }
    """
