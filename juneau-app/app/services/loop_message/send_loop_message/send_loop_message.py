import requests
from requests import Response
import json
import os
from dotenv import load_dotenv
import argparse

# Load environment variables from .env file if it exists
load_dotenv()

loop_api_key = os.getenv("LOOP_API_KEY")
loop_auth_key = os.getenv("LOOP_AUTH_KEY")
phone_number = os.getenv("PHONE_NUMBER")

def send_message(recipient, text, sender_name=None, 
                 attachments=None, timeout=None, passthrough=None,
                 status_callback=None, status_callback_header=None,
                 reply_to_id=None, subject=None, effect=None, service="imessage"):
    """
    Send a message via the iMessage Conversation API
    """
    sender_name = sender_name or os.getenv("IMESSAGE_SENDER_NAME")
    
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

def send_group_message(group_id, text, sender_name=None, api_key=None, secret_key=None,
                      attachments=None, timeout=None, passthrough=None,
                      status_callback=None, status_callback_header=None):
    """
    Send a message to an iMessage group
    """
    api_key = api_key or os.getenv("IMESSAGE_API_KEY")
    secret_key = secret_key or os.getenv("IMESSAGE_SECRET_KEY")
    sender_name = sender_name or os.getenv("IMESSAGE_SENDER_NAME")
    
    url = "https://server.loopmessage.com/api/v1/message/send/"
    
    headers = {
        "Authorization": api_key,
        "Loop-Secret-Key": secret_key,
        "Content-Type": "application/json"
    }
    
    payload = {
        "group": group_id,
        "text": text,
        "sender_name": sender_name
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
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}

def send_audio_message(recipient, text, media_url, sender_name=None, api_key=None, secret_key=None,
                       status_callback=None, status_callback_header=None, passthrough=None):
    """
    Send an audio message
    """
    api_key = api_key or os.getenv("IMESSAGE_API_KEY")
    secret_key = secret_key or os.getenv("IMESSAGE_SECRET_KEY")
    sender_name = sender_name or os.getenv("IMESSAGE_SENDER_NAME")
    
    url = "https://server.loopmessage.com/api/v1/message/send/"
    
    headers = {
        "Authorization": api_key,
        "Loop-Secret-Key": secret_key,
        "Content-Type": "application/json"
    }
    
    payload = {
        "recipient": recipient,
        "text": text,
        "media_url": media_url,
        "sender_name": sender_name,
        "audio_message": True
    }
    
    if status_callback:
        payload["status_callback"] = status_callback
    if status_callback_header:
        payload["status_callback_header"] = status_callback_header
    if passthrough:
        payload["passthrough"] = passthrough
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}

def send_reaction(recipient, text, message_id, reaction, sender_name=None, api_key=None, secret_key=None,
                 status_callback=None, status_callback_header=None, passthrough=None):
    """
    Send a reaction to a message
    """
    api_key = api_key or os.getenv("IMESSAGE_API_KEY")
    secret_key = secret_key or os.getenv("IMESSAGE_SECRET_KEY")
    sender_name = sender_name or os.getenv("IMESSAGE_SENDER_NAME")
    
    url = "https://server.loopmessage.com/api/v1/message/send/"
    
    headers = {
        "Authorization": api_key,
        "Loop-Secret-Key": secret_key,
        "Content-Type": "application/json"
    }
    
    payload = {
        "recipient": recipient,
        "text": text,
        "message_id": message_id,
        "sender_name": sender_name,
        "reaction": reaction
    }
    
    if status_callback:
        payload["status_callback"] = status_callback
    if status_callback_header:
        payload["status_callback_header"] = status_callback_header
    if passthrough:
        payload["passthrough"] = passthrough
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":

    response = send_message(
        recipient=phone_number,
        text="Hello from Loop Message!",
        sender_name="Loop Message Sender",
    )
    
    print(response)