# AWS Access Key Rotation

This Python script automates the process of rotating AWS access keys for IAM users in an AWS account. It also sends an email to the IAM user with the new access key, and sends a message to a monitoring Slack channel if any access keys are older than 90 days.

## Prerequisites

- Python 3
- Boto3 library
- AWS IAM user with appropriate permissions

## Configuration

Before running the script, update the following variables:

- `threshold_days`: The number of days after which access keys should be rotated. The default value is 90.
- `SENDER_EMAIL`: The email address from which to send the email to IAM users. Set as an environment variable.
- `webhook_url`: The URL of the Slack webhook to which to send the message if any access keys are older than 90 days.

## Usage

To run the script, use the following command:

```
python aws_access_key_rotation.py
```

The script will loop through all IAM users in the AWS account and rotate any access keys that are older than the specified threshold. It will also send an email to the user with the new access key, and send a message to the monitoring Slack channel if any access keys are older than the threshold. Only Users tagged with Key: UserType and Value: employee are affected.
