import requests
import boto3
import json
import os
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError

# Initialize AWS clients outside of the handler for connection reuse
s3_client = boto3.client('s3')
s3_resource = boto3.resource('s3')

def fetch_data(url):
    """Fetches JSON data from the provided API URL."""
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises HTTPError for bad responses
        json_response = response.json()
        return json_response.get("data", [])
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def check_or_create_bucket(bucket_name):
    """Checks if the bucket exists. If not, it creates the bucket."""
    try:
        s3_resource.meta.client.head_bucket(Bucket=bucket_name)
        print(f"Bucket '{bucket_name}' already exists.")
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == '404':  # Bucket does not exist
            try:
                s3_client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': os.getenv('AWS_REGION', 'ap-southeast-2')}
                )
                print(f"Bucket '{bucket_name}' created successfully.")
            except Exception as e:
                print(f"Error creating bucket '{bucket_name}': {e}")
                return False
        else:
            print(f"Error checking bucket '{bucket_name}': {e}")
            return False
    return True

def upload_to_s3(data, bucket, file_name):
    """Uploads data to the specified S3 bucket."""
    try:
        if check_or_create_bucket(bucket):
            s3_client.put_object(
                Bucket=bucket,
                Key=file_name,
                Body=json.dumps(data),
                ContentType='application/json'
            )
            print(f"File uploaded successfully to {bucket}/{file_name}")
    except (NoCredentialsError, PartialCredentialsError):
        print("AWS credentials not found or incomplete. Please configure your credentials.")
    except Exception as e:
        print(f"Error uploading file to S3: {e}")

def lambda_handler(event, context):
    """AWS Lambda function entry point."""
    # Retrieve values from environment variables
    api_url = os.getenv("API_URL", "https://datausa.io/api/data?drilldowns=Nation&measures=Population")
    bucket_name = os.getenv("S3_BUCKET_NAME", "bls-gov-dataset")  # Default bucket name
    s3_file_name = os.getenv("S3_FILE_NAME", "datausa_population.json")

    if not bucket_name:
        print("S3 bucket name not provided.")
        return

    # Fetch data from API
    data = fetch_data(api_url)
    if data:
        # Upload data to S3
        upload_to_s3(data, bucket_name, s3_file_name)
    else:
        print("No data fetched; skipping upload.")
