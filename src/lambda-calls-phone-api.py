# Version: Python 3.9 (verified)
# Import libraries
import json, os
import boto3
import urllib3 # The requests library is desperated in Lambda, so we need to use urllib3
# For logging and trace
import logging, traceback
import time
from base64 import b64decode # For data decryption
from botocore.exceptions import ClientError # For Exception handling

# Environment variables
notify_url = os.environ['notify_url']
token_secret_name = os.environ['token_secret_name']
max_tries = int(os.environ['max_tries'])
wait_secs = int(os.environ['wait_secs'])
template = os.environ['template']
input_receivers = os.environ['receivers']

# System variables
aws_region = os.environ['AWS_DEFAULT_REGION']

# Retrieve token from Amazon Secrets Manager
def get_secret(secret_name, region_name):

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'DecryptionFailureException':
            # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InternalServiceErrorException':
            # An error occurred on the server side.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            # You provided an invalid value for a parameter.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            # You provided a parameter value that is not valid for the current state of the resource.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'ResourceNotFoundException':
            # We can't find the resource that you asked for.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
    else:
        # Decrypts secret using the associated KMS key.
        # Depending on whether the secret is a string or binary, one of these fields will be populated.
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
            decoded_binary_secret = ''
        else:
            decoded_binary_secret = base64.b64decode(get_secret_value_response['SecretBinary'])
            secret = decoded_binary_secret
            
    return secret

secrets = get_secret(token_secret_name, aws_region)

if secrets != '':
    secrets = json.loads(secrets)

if 'api_token' in secrets:
    token = secrets['api_token']
    receivers = secrets['default_receiver']

# Request headers
authorization = 'Token ' + token
headers = {'Accept': 'application/json', 'Content-type':'application/json', 'Authorization': authorization}

# Create a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Message class
class Message:
    def __init__(self, receivers, subject, body, template):
        self.receivers = receivers
        self.subject = subject
        self.body = body
        self.template = template

    def send(self):
        # @TODO Construct the message based on configurations of the 3rd-party API.
        messages = {"template": self.template, "content": self.body, "receivers": self.receivers}

        # Logging
        logger.info(self.receivers + " " + self.body)

        # Send a POST request via urllib3
        http = urllib3.PoolManager(timeout=1.0, retries=False)

        response = http.request('POST', notify_url, headers=headers, body=json.dumps(messages))

        # return HTTP response
        return response

### Lambda Handler begins ###
def lambda_handler(event, context):
    # Debug information
    print("Received event: " + json.dumps(event, indent=2))
    # Example: sns_message = json.loads(event['Records'][0]['Sns']['Message'])

    # Default error repsonse
    output_message = 'Calling the API Failed!'

    try:
        # @TODO get parameters from the event object
        # receivers = os.environ['receivers']
        subject   = os.environ['subject']
        body      = os.environ['body']

        print("Receivers: ", receivers)
        print("Subject: ", subject)
        print("Body: ", body)
    except:
        e = traceback.format_exc()
        # Logging
        logging.error(e)

    attempts = 0
    success = False

    # Create a message object
    message = Message(receivers, subject, body, template)

    while attempts < max_tries:
        attempts += 1
        try:
            r = message.send()  # Send the message

            if r.status < 500:
                
                if r.status == 200:
                    success = True
                    output_message = 'Calling the API Succeeded!'

                else: # Other types of errors, but end the loop
                    # Log the error
                    output_message = 'Error: ' + str(r.data)
            break

        # except:
        except urllib3.exceptions.NewConnectionError as e:
            # Log the error
            logger.debug(e)
            logger.debug("Resend message " + str(attempts) + " times!")

        time.sleep(wait_secs)

        if attempts == max_tries:
            break

    if success:
        return {
            'statusCode': 200,
            'body': json.dumps(output_message)
        }
    else:
        return {
            'statusCode': 400,
            'body': json.dumps(output_message)
        }
### Lambda Handler ends here
