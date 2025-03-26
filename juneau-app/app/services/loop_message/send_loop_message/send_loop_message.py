import requests
from requests import Response
import json
import os
import argparse

import boto3

environment = os.getenv("environment")


def set_secrets():
    if environment == "local":
        from dotenv import load_dotenv
        load_dotenv()
        loop_api_key = os.getenv("LOOP_API_KEY")
        loop_auth_key = os.getenv("LOOP_AUTH_KEY")
    else:
        loop_secret_name = os.getenv("loop_secret_name")
        secrets_manager = boto3.client("secretsmanager")
        get_secret_value_response = secrets_manager.get_secret_value(
            SecretId=loop_secret_name
        )
        secret_string = get_secret_value_response["SecretString"]
        secret_dict = json.loads(secret_string)
        loop_api_key = secret_dict.get("LOOP_API_KEY")
        loop_auth_key = secret_dict.get("LOOP_AUTH_KEY")
    return loop_api_key, loop_auth_key

# Load secrets from AWS Secrets Manager or .env file
loop_api_key, loop_auth_key = set_secrets()
        

def send_message(recipient, text, sender_name=None, 
                 attachments=None, timeout=None, passthrough=None,
                 status_callback=None, status_callback_header=None,
                 reply_to_id=None, subject=None, effect=None, service="imessage"):
    """
    Send a message via the iMessage Conversation API
    """
    sender_name = "Loop Message Sender" if sender_name is None else sender_name
    
    if not loop_api_key or not loop_auth_key or not sender_name:
        raise ValueError("API key, Secret key, and Sender name are required")
    
    url = "https://server.loopmessage.com/api/v1/message/send/"
    
    headers = {
        "Authorization": loop_auth_key,
        "Loop-Secret-Key": loop_api_key,
        "Content-Type": "application/json"
    }
    
    payload = {
        "recipient": recipient,
        "text": text,
        "sender_name": sender_name,
        "service": service
    }
    
    if attachments:
        payload["attachments"] = attachments
    if timeout:
        payload["timeout"] = timeout
    if passthrough:
        payload["passthrough"] = passthrough
    if status_callback:
        payload["status_callback"] = status_callback
    if status_callback_header:
        payload["status_callback_header"] = status_callback_header
    if reply_to_id:
        payload["reply_to_id"] = reply_to_id
    if subject:
        payload["subject"] = subject
    if effect:
        payload["effect"] = effect
    
    try:
        response: Response = requests.post(url, headers=headers, json=payload)
        return {
            "status_code": response.status_code,
            "response": response.json()
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def lambda_handler(event, context):
    """
    AWS Lambda handler function that calls send_message with the provided event parameters
    """
    print(    "Received event: {}".format(event))    
    
    # Extract parameters from the event
    recipient = event.get('recipient')
    text = event.get('text')
    sender_name = event.get('sender_name')
    attachments = event.get('attachments')
    timeout = event.get('timeout')
    passthrough = event.get('passthrough')
    status_callback = event.get('status_callback')
    status_callback_header = event.get('status_callback_header')
    reply_to_id = event.get('reply_to_id')
    subject = event.get('subject')
    effect = event.get('effect')
    service = event.get('service', 'imessage')
    
    # Call the send_message function with the extracted parameters
    result = send_message(
        recipient=recipient,
        text=text,
        sender_name=sender_name,
        attachments=attachments,
        timeout=timeout,
        passthrough=passthrough,
        status_callback=status_callback,
        status_callback_header=status_callback_header,
        reply_to_id=reply_to_id,
        subject=subject,
        effect=effect,
        service=service
    )
    
    return result

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Send a message via the iMessage Conversation API")
    parser.add_argument("recipient", help="Recipient's phone number or email address")
    parser.add_argument("text", help="Text message to send")
    parser.add_argument("--sender_name", help="Sender's name")
    parser.add_argument("--attachments", nargs='+', help="List of attachment URLs")
    parser.add_argument("--timeout", type=int, help="Timeout in seconds")
    parser.add_argument("--passthrough", help="Passthrough data")
    parser.add_argument("--status_callback", help="URL for status callback")
    parser.add_argument("--status_callback_header", help="Header for status callback")
    parser.add_argument("--reply_to_id", help="ID of the message to reply to")
    parser.add_argument("--subject", help="Subject of the message")
    parser.add_argument("--effect", help="Effect for the message")
    parser.add_argument("--service", default="imessage", help="Service to use (default: imessage)")
    args = parser.parse_args()
    
    request = {
        "recipient": args.recipient,
        "text": args.text,
        "sender_name": args.sender_name,
        "attachments": args.attachments,
        "timeout": args.timeout,
        "passthrough": args.passthrough,
        "status_callback": args.status_callback,
        "status_callback_header": args.status_callback_header,
        "reply_to_id": args.reply_to_id,
        "subject": args.subject,
        "effect": args.effect,
        "service": args.service
    }
    result = lambda_handler(request, None)
    print(result)
    
    
    
# def send_group_message(group_id, text, sender_name=None, api_key=None, secret_key=None,
#                       attachments=None, timeout=None, passthrough=None,
#                       status_callback=None, status_callback_header=None):
#     """
#     Send a message to an iMessage group
#     """
#     api_key = api_key or os.getenv("IMESSAGE_API_KEY")
#     secret_key = secret_key or os.getenv("IMESSAGE_SECRET_KEY")
#     sender_name = sender_name or os.getenv("IMESSAGE_SENDER_NAME")
    
#     url = "https://server.loopmessage.com/api/v1/message/send/"
    
#     headers = {
#         "Authorization": api_key,
#         "Loop-Secret-Key": secret_key,
#         "Content-Type": "application/json"
#     }
    
#     payload = {
#         "group": group_id,
#         "text": text,
#         "sender_name": sender_name
#     }
    
#     if attachments:
#         payload["attachments"] = attachments
#     if timeout:
#         payload["timeout"] = timeout
#     if passthrough:
#         payload["passthrough"] = passthrough
#     if status_callback:
#         payload["status_callback"] = status_callback
#     if status_callback_header:
#         payload["status_callback_header"] = status_callback_header
    
#     try:
#         response = requests.post(url, headers=headers, json=payload)
#         return response.json()
#     except Exception as e:
#         return {"success": False, "error": str(e)}

# def send_audio_message(recipient, text, media_url, sender_name=None, api_key=None, secret_key=None,
#                        status_callback=None, status_callback_header=None, passthrough=None):
#     """
#     Send an audio message
#     """
#     api_key = api_key or os.getenv("IMESSAGE_API_KEY")
#     secret_key = secret_key or os.getenv("IMESSAGE_SECRET_KEY")
#     sender_name = sender_name or os.getenv("IMESSAGE_SENDER_NAME")
    
#     url = "https://server.loopmessage.com/api/v1/message/send/"
    
#     headers = {
#         "Authorization": api_key,
#         "Loop-Secret-Key": secret_key,
#         "Content-Type": "application/json"
#     }
    
#     payload = {
#         "recipient": recipient,
#         "text": text,
#         "media_url": media_url,
#         "sender_name": sender_name,
#         "audio_message": True
#     }
    
#     if status_callback:
#         payload["status_callback"] = status_callback
#     if status_callback_header:
#         payload["status_callback_header"] = status_callback_header
#     if passthrough:
#         payload["passthrough"] = passthrough
    
#     try:
#         response = requests.post(url, headers=headers, json=payload)
#         return response.json()
#     except Exception as e:
#         return {"success": False, "error": str(e)}

# def send_reaction(recipient, text, message_id, reaction, sender_name=None, api_key=None, secret_key=None,
#                  status_callback=None, status_callback_header=None, passthrough=None):
#     """
#     Send a reaction to a message
#     """
#     api_key = api_key or os.getenv("IMESSAGE_API_KEY")
#     secret_key = secret_key or os.getenv("IMESSAGE_SECRET_KEY")
#     sender_name = sender_name or os.getenv("IMESSAGE_SENDER_NAME")
    
#     url = "https://server.loopmessage.com/api/v1/message/send/"
    
#     headers = {
#         "Authorization": api_key,
#         "Loop-Secret-Key": secret_key,
#         "Content-Type": "application/json"
#     }
    
#     payload = {
#         "recipient": recipient,
#         "text": text,
#         "message_id": message_id,
#         "sender_name": sender_name,
#         "reaction": reaction
#     }
    
#     if status_callback:
#         payload["status_callback"] = status_callback
#     if status_callback_header:
#         payload["status_callback_header"] = status_callback_header
#     if passthrough:
#         payload["passthrough"] = passthrough
    
#     try:
#         response = requests.post(url, headers=headers, json=payload)
#         return response.json()
#     except Exception as e:
#         return {"success": False, "error": str(e)}
