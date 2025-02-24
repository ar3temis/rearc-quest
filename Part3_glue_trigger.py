import json
import boto3

sqs = boto3.client('sqs')
glue = boto3.client('glue')

QUEUE_URL = "https://sqs.ap-southeast-2.amazonaws.com/842675998286/s3_event_queue"
GLUE_JOB_NAME = "Data_analysis"  # Replace with your actual Glue Job name

def lambda_handler(event, context):
    print("Received event: ", json.dumps(event))

    for record in event['Records']:
        message_body = json.loads(record['body'])  # Extract the SQS message
        print("Message Body: ", message_body)

        # Trigger Glue Job
        response = glue.start_job_run(JobName=GLUE_JOB_NAME)
        print("Glue Job Started: ", response)

    return {"statusCode": 200, "body": "Glue job triggered successfully!"}
