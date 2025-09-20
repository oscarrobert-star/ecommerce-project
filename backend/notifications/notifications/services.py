import os
import boto3
import logging
from botocore.exceptions import BotoCoreError, ClientError

logger = logging.getLogger("notification_service")

aws_region = os.getenv("AWS_REGION", "us-east-1")

# Use default session (works with ~/.aws locally, and ECS task roles in AWS)
sns_client = boto3.client("sns", region_name=aws_region)
ses_client = boto3.client("ses", region_name=aws_region)


def send_sms(recipient: str, message: str) -> dict:
    """
    Send SMS using AWS SNS.
    recipient: phone number in E.164 format (+2547XXXXXXX)
    """
    logger.info("Attempting to send SMS", extra={"recipient": recipient, "length": len(message)})
    try:
        response = sns_client.publish(
            PhoneNumber=recipient,
            Message=message,
            MessageAttributes={
                "AWS.SNS.SMS.SenderID": {
                    "DataType": "String",
                    "StringValue": os.getenv("SNS_SENDER_ID", "OkiyaLabs"),
                },
                "AWS.SNS.SMS.SMSType": {
                    "DataType": "String",
                    "StringValue": "Transactional",
                },
            },
        )
        message_id = response.get("MessageId")
        logger.info("SMS sent successfully", extra={"recipient": recipient, "message_id": message_id})
        return {"status": "sent", "message_id": message_id}
    except (BotoCoreError, ClientError) as e:
        logger.error("SMS send failed", extra={"recipient": recipient, "error": str(e)})
        return {"status": "failed", "error": str(e)}


def send_email(recipient: str, subject: str, message: str) -> dict:
    """
    Send email using AWS SES.
    recipient: email address
    """
    sender = os.getenv("SES_SENDER_EMAIL", "shop@okiyalabs.click")
    logger.info("Attempting to send Email", extra={"recipient": recipient, "subject": subject})
    try:
        response = ses_client.send_email(
            Source=sender,
            Destination={"ToAddresses": [recipient]},
            Message={
                "Subject": {"Data": subject},
                "Body": {"Text": {"Data": message}},
            },
        )
        message_id = response.get("MessageId")
        logger.info("Email sent successfully", extra={"recipient": recipient, "message_id": message_id})
        return {"status": "sent", "message_id": message_id}
    except (BotoCoreError, ClientError) as e:
        logger.error("Email send failed", extra={"recipient": recipient, "error": str(e)})
        return {"status": "failed", "error": str(e)}
