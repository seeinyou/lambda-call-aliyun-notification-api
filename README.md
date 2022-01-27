# Call a 3rd-party phone call notification API via a Lambda function

# Introduction
For business-critical IT resources, a phone call notification is necessary to minimize the response time of the ops team in some scenarios. However, not all cloud vendors offer appropriate methods/services to make send notifications via phone calls. As a result, we use 3rd-party services via APIs to implement the phone call notification mechanism.

The solution leverages CloudWatch alarms to send a message to an Amazon SNS topic, which is subscribed by an Amazon Lambda function when the CloudWatch alarm is triggered by the change of status of AWS resources. The Lambda function retrieves information in the message from a group of parameters, and send an HTTPS POST request to the 3rd-party notification system API. The 3rd-party notification system makes a phone call to a group of pre-configured telephone/mobile numbers after receiving a successful API call.

# Files

## Lambda functions

## src

- lambda-call-aliyun-phone-api.py - Extract information from SNS messages, form parameters, and call **Aliyun phone call API**.

