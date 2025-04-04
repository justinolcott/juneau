import argparse
import boto3
import json
import os
import requests

ENVIRONMENT = os.getenv("ENVIRONMENT", "local")
if ENVIRONMENT == "local":
    from dotenv import load_dotenv
    load_dotenv(".env.development")


def set_secrets():
    if ENVIRONMENT == "local":
        from dotenv import load_dotenv
        load_dotenv()
        LOOP_API_KEY = os.getenv("LOOP_API_KEY")
        LOOP_AUTH_KEY = os.getenv("LOOP_AUTH_KEY")
    else:
        LOOP_SECRET_NAME = os.getenv("LOOP_SECRET_NAME")
        secrets_manager = boto3.client("secretsmanager")
        get_secret_value_response = secrets_manager.get_secret_value(
            SecretId=LOOP_SECRET_NAME
        )
        secret_string = get_secret_value_response["SecretString"]
        secret_dict = json.loads(secret_string)
        LOOP_API_KEY = secret_dict.get("LOOP_API_KEY")
        LOOP_AUTH_KEY = secret_dict.get("LOOP_AUTH_KEY")
    return LOOP_API_KEY, LOOP_AUTH_KEY

LOOP_API_KEY, LOOP_AUTH_KEY = set_secrets()
        

def send_message(recipient, text, sender_name=None, 
                 attachments=None, timeout=None, passthrough=None,
                 status_callback=None, status_callback_header=None,
                 reply_to_id=None, subject=None, effect=None, service="imessage"):
    """
    Send a message via the iMessage Conversation API
    """
    sender_name = "Loop Message Sender" if sender_name is None else sender_name
    
    if not LOOP_API_KEY or not LOOP_AUTH_KEY or not sender_name:
        raise ValueError("API key, Secret key, and Sender name are required")
    
    url = "https://server.loopmessage.com/api/v1/message/send/"
    
    headers = {
        "Authorization": LOOP_AUTH_KEY,
        "Loop-Secret-Key": LOOP_API_KEY,
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
        print(f"Sending message to {recipient} with payload: {payload}")
        response: requests.Response = requests.post(url, headers=headers, json=payload)
        return {
            "status_code": response.status_code,
            "response": response.json()
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def lambda_handler(event, context):
    try:
        if 'Records' in event and len(event['Records']) > 0:
            for record in event['Records']:
                # This is an SQS event
                payload = json.loads(record['body'])
                recipient = payload.get('recipient')
                text = payload.get('text')
                sender_name = payload.get('sender_name')
                attachments = payload.get('attachments')
                timeout = payload.get('timeout')
                passthrough = payload.get('passthrough')
                status_callback = payload.get('status_callback')
                status_callback_header = payload.get('status_callback_header')
                reply_to_id = payload.get('reply_to_id')
                subject = payload.get('subject')
                effect = payload.get('effect')
                service = payload.get('service', 'imessage')
                
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
        else:
            raise ValueError("No records found in the event")
    except json.JSONDecodeError:
        return {"success": False, "error": "Failed to parse JSON payload"}
    
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
        "Records": [
            {
                "body": json.dumps({
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
                })
            }
        ]
    }
    result = lambda_handler(request, None)
    print(result)