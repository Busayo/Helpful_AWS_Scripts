import boto3
import requests, json
import pytz
from datetime import datetime
import csv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os.path


def send_email(email_recipient,
            email_subject,
            email_message,
            attachment_location = '.'):
    """
    Sends an email to the specified recipient with the specified subject and message.
    If an attachment location is specified, the function attaches the file to the email.
    """
    email_sender = os.environ.get('SENDER_EMAIL')

    msg = MIMEMultipart()
    msg['From'] = email_sender
    msg['To'] = email_recipient
    msg['Subject'] = email_subject

    msg.attach(MIMEText(email_message, 'plain'))

    if attachment_location != '.':
        filename = os.path.basename(attachment_location)
        attachment = open(attachment_location, "rb")
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition',
                        "attachment; filename= %s" % filename)
        msg.attach(part)


iam_client = boto3.client('iam')

response = iam_client.list_users()

threshold_days = 90
users_exceeding_threshold = []

# Loop through all the users in the AWS account
for user in response['Users']:
    user_tags = iam_client.list_user_tags(UserName=user['UserName'])['Tags']
    # Check if the user is an employee
    if any(tag['Key'] == 'UserType' and tag['Value'] == 'employee' for tag in user_tags):
        print(f"User: {user['UserName']}")
        access_keys = iam_client.list_access_keys(UserName=user['UserName'])
        # Loop through all the access keys for the user
        for key in access_keys['AccessKeyMetadata']:
            key_id = key['AccessKeyId']
            create_date = key['CreateDate'].replace(tzinfo=pytz.UTC)
            active_days = (datetime.now(pytz.UTC) - create_date).days
            print(f"\tKey: {key_id}, Active for {active_days} days")
            # Check if the access key is older than 90 days
            if active_days > threshold_days:
                # Create a new access key for the user
                new_key = iam_client.create_access_key(UserName=user['UserName'])['AccessKey']
                print(f"\tCreated new key:\n\tAccess Key ID: {new_key['AccessKeyId']}\n\tSecret Access Key: {new_key['SecretAccessKey']}")
                # Write the new access key to a CSV file
                with open(f"{user['UserName']}.csv", mode='w') as csv_file:
                    fieldnames = ['User Name', 'Access Key ID', 'Secret Access Key']
                    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

                    writer.writeheader()
                    writer.writerow({'User Name': user['UserName'], 'Access Key ID': new_key['AccessKeyId'], 'Secret Access Key': new_key['SecretAccessKey']})

                    # Send an email to the user with the new access key
                    send_email(f"{user['UserName']}@company.com",
                                'AWS ACCESS KEY QUARTERLY ROTATION',
                                'Kindly get your access key ID and Secret Key from the attached CSV. \
                                Use the AWS command "aws configure". Please note that your previous access key will be deactivated in 3 days. \
                                Kindly reach out to the Operations team if you have further questions.',
                                f"{user['UserName']}.csv")
    else:
        access_keys = iam_client.list_access_keys(UserName=user['UserName'])
        # Loop through all the access keys for the users
        for key in access_keys['AccessKeyMetadata']:
            key_id = key['AccessKeyId']
            create_date = key['CreateDate'].replace(tzinfo=pytz.UTC)
            active_days = (datetime.now(pytz.UTC) - create_date).days
            print(f"User: {user['UserName']}\n\tKey: {key_id}, Active for {active_days} days")
            # Check if the access key is older than 90 days
            if active_days > threshold_days:
                users_exceeding_threshold.append(user['UserName'])
# if any access keys are older than 90 days, send a list of the said users as well as their access IDs to the monitoring slack channel
if len(users_exceeding_threshold) > 0:
    # insert webhook url or save as env var
    webhook_url = "insert webhook_url"
    message = {
        "text": f"The following users have exceeded the threshold of {threshold_days} days:\n{', '.join(users_exceeding_threshold)}"
    }
    try:
        response = requests.post(webhook_url, data=json.dumps(message))
        print("Message sent: ", response.text)
    except requests.exceptions.HTTPError as e:
        print(f"Error sending message: {e}")
