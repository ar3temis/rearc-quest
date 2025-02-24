import os
import urllib.request
import re
import boto3
import hashlib
from botocore.exceptions import ClientError

# Configuration
BLS_URL = "https://download.bls.gov/pub/time.series/pr/"
LOCAL_DIR = "/tmp/"  # AWS Lambda only allows writes here
USER_AGENT = "niharika.singh0625@gmail.com"

# S3 Configuration (Dynamic)
UPLOAD_TO_S3 = True
S3_BUCKET = os.getenv("S3_BUCKET_NAME","bls-gov-dataset")  # Fetch bucket name from environment variable
S3_PREFIX = os.getenv("S3_PREFIX", "bls-data/")  # Folder inside the bucket (default: bls-data/)
AWS_REGION = os.getenv("AWS_REGION", "ap-southeast-2")  # Fetch AWS region (default to us-east-1)

# Initialize S3 client
s3_client = boto3.client("s3")
s3_resource = boto3.resource("s3")


def check_or_create_bucket(bucket_name, region):
    """Checks if the bucket exists, and creates it if it does not exist."""
    try:
        s3_resource.meta.client.head_bucket(Bucket=bucket_name)
        print(f"Bucket '{bucket_name}' already exists.")
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "404":
            try:
                s3_client.create_bucket(bucket_name,"ap-southeast-2")
                print(f"Bucket '{bucket_name}' created successfully in region {region}.")
            except Exception as e:
                print(f"Error creating bucket '{bucket_name}': {e}")
                return False
        else:
            print(f"Error checking bucket '{bucket_name}': {e}")
            return False
    return True


def generate_file_hash(file_path):
    """Generates a hash for a file's content."""
    hasher = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def fetch_bls_files():
    """Fetch all files from the BLS Productivity directory and save them locally."""
    headers = {"User-Agent": USER_AGENT}
    req = urllib.request.Request(BLS_URL, headers=headers)

    os.makedirs(LOCAL_DIR, exist_ok=True)  # Ensure /tmp/ exists

    try:
        with urllib.request.urlopen(req) as response:
            html_content = response.read().decode("utf-8")
    except Exception as e:
        raise Exception(f"Failed to fetch directory listing: {e}")

    # Extract file names
    file_links = re.findall(r'<A HREF="/pub/time.series/pr/(pr\.[^"]+)">', html_content)

    if not file_links:
        print("No files found. Check if the HTML structure has changed.")
        return []

    print(f"Found {len(file_links)} files. Starting downloads...")

    downloaded_files = []
    for filename in file_links:
        file_url = BLS_URL + filename
        local_file_path = os.path.join(LOCAL_DIR, filename)

        try:
            req_file = urllib.request.Request(file_url, headers=headers)
            with urllib.request.urlopen(req_file) as file_response, open(
                local_file_path, "wb"
            ) as f:
                f.write(file_response.read())

            downloaded_files.append(local_file_path)
            print(f"Downloaded: {filename}")

        except Exception as e:
            print(f"Failed to download: {filename}, Error: {e}")

    print(f"Downloaded {len(downloaded_files)} files successfully.")
    return downloaded_files


def list_s3_files(bucket, prefix):
    """Lists all files in the specified S3 bucket under the given prefix."""
    try:
        response = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
        if "Contents" in response:
            return {obj["Key"]: obj["ETag"].strip('"') for obj in response["Contents"]}
        return {}
    except Exception as e:
        print(f"Error listing files in S3: {e}")
        return {}


def upload_to_s3(file_path, file_name, bucket):
    """Uploads a file to S3 and logs success or failure."""
    s3_key = S3_PREFIX + file_name  # Construct S3 path (e.g., bls-data/pr.class)

    try:
        file_hash = generate_file_hash(file_path)
        existing_files = list_s3_files(bucket, S3_PREFIX)

        if s3_key in existing_files and existing_files[s3_key] == file_hash:
            print(f"Skipping upload (no changes detected): {s3_key}")
            return

        s3_client.upload_file(file_path, bucket, s3_key)
        print(f"Uploaded to S3: s3://{bucket}/{s3_key}")
    except Exception as e:
        print(f"Error uploading {file_name} to S3: {e}")


def delete_old_s3_files(existing_files, downloaded_files, bucket):
    """Deletes files from S3 that no longer exist in the latest BLS data."""
    downloaded_file_names = {os.path.basename(f) for f in downloaded_files}
    for s3_key in existing_files.keys():
        s3_file_name = os.path.basename(s3_key)
        if s3_file_name not in downloaded_file_names:
            try:
                s3_client.delete_object(Bucket=bucket, Key=s3_key)
                print(f"Deleted outdated file from S3: {s3_key}")
            except Exception as e:
                print(f"Error deleting {s3_key} from S3: {e}")


def lambda_handler(event, context):
    """AWS Lambda entry point."""
    if not S3_BUCKET:
        print("S3 bucket name is missing. Set S3_BUCKET_NAME as an environment variable.")
        return {"statusCode": 400, "body": "S3 bucket name is required."}

    try:
        # Ensure bucket exists
        if not check_or_create_bucket(S3_BUCKET, AWS_REGION):
            return {"statusCode": 500, "body": "Failed to create or verify S3 bucket."}

        downloaded_files = fetch_bls_files()
        if not downloaded_files:
            return {"statusCode": 500, "body": "No files were downloaded."}

        existing_s3_files = list_s3_files(S3_BUCKET, S3_PREFIX)

        # Upload new/modified files
        for local_file in downloaded_files:
            file_name = os.path.basename(local_file)
            upload_to_s3(local_file, file_name, S3_BUCKET)

        # Delete outdated files
        delete_old_s3_files(existing_s3_files, downloaded_files, S3_BUCKET)

        return {
            "statusCode": 200,
            "body": f"Downloaded {len(downloaded_files)} files, uploaded to S3, and removed obsolete files."
        }
    except Exception as e:
        return {"statusCode": 500, "body": str(e)}
