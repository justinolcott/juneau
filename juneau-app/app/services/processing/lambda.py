import boto3
import BytesIO
import hashlib
import json
import os
import requests

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, trim_messages, utils
from langchain_google_genai import ChatGoogleGenerativeAI
from re import Match, match
from typing import Union
from urllib.parse import urlparse


GEMINI_MODEL = "gemini-2.0-flash"  # 1M context window
ENVIRONMENT = os.getenv("ENVIRONMENT", "local")
SQS_NAME = os.getenv("SQS_NAME")

def set_secrets():
    if ENVIRONMENT == "local":
        load_dotenv(".env.development")
        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    else:
        GEMINI_SECRET_NAME = os.getenv("GEMINI_SECRET_NAME")
        secrets_manager = boto3.client("secretsmanager")
        get_secret_value_response = secrets_manager.get_secret_value(
            SecretId=GEMINI_SECRET_NAME
        )
        secret_string = get_secret_value_response['SecretString']
        secret_dict = json.loads(secret_string)
        GEMINI_API_KEY = secret_dict.get("GEMINI_API_KEY")
    return GEMINI_API_KEY

GOOGLE_API_KEY = set_secrets()
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

db_client = boto3.resource('dynamodb')


def format_human_request(usr_request):

    phone_id = int(usr_request["recipient"][1:])  # "+15555555555" --> 5555555555
    try:
        text_message = usr_request['attachments']  # would be a public Google firebase URL
    except KeyError:
        text_message = usr_request["text"]

        chat_count = get_chat_count(phone_id)
        new_chat:Union[Match|None] = match('✨', text_message)
        if new_chat:  # update chat_id += 1
            chat_count += 1
            write_chat_count(phone_id, chat_count)

    return {
    'phone': phone_id,
    'chat_id': chat_count,
    'text': text_message,
    'human': True,
    'language': usr_request["language"]["code"],
    'timestamp': 1712580000  # TO DO: implement real timestamping
    }

def write_to_chat(formatted_request):
    table = db_client.Table('UserConversations')
    response = table.update_item(
        Key={
            'phone': formatted_request['phone'],
            'chat_id':  formatted_request['chat_id']  # new sort key
        },
        UpdateExpression='SET messages = list_append(if_not_exists(messages, :empty_list), :new_messages)',
        ExpressionAttributeValues={
            ':new_messages': [(formatted_request['text'], formatted_request['human'])],
            ':empty_list': []
        },
        ReturnValues='UPDATED_NEW'
    )
    return response

def gather_context(formatted_request):
    table = db_client.Table('UserConversations')
    # Gather all context from table
    chat_list = table.get_item(
        Key={
            'phone': formatted_request['phone'],
            'chat_id': formatted_request['chat_id'],
        })
    formatted_chat = chat_list['Item']['messages']
    return formatted_chat

def get_chat_count(phone_number:int):
    table = db_client.Table("UserChats")
    response = table.get_item(Key={'phone': phone_number})
    item = response.get('Item', {})
    return item.get('my_int_attribute', 0)

def write_chat_count(phone_number:int, chat_id:int):
    table = db_client.Table("UserChats")
    response = table.update_item(
        Key={'phone':phone_number},
        UpdateExpression='SET my_int_attribute = :newval',
        ExpressionAttributeValues={':newval': chat_id})
    return response


def invoke_model(payload, ):
    sys_prompt = "As my AI assistant, answer my texts succinctly and try to match my tone.\n"
    system_message = SystemMessage(content=sys_prompt)
    try:        
        messages = [system_message]
        for text in payload:
            if text[1]:
                messages.append(HumanMessage(content=text[0]))
            else:
                messages.append(AIMessage(content=text[0]))
        
        # Limit messages to certain token window
        messages = trim_messages(
            messages,
            max_tokens=16000,  # Could do 1M, but that's not practical for response times nor for the texting modality; 16k should be plenty.
            strategy="last",
            token_counter=utils.count_tokens_approximately,
            start_on="human",
            include_system=True,
            allow_partial=False,
        )

        model = ChatGoogleGenerativeAI(model=GEMINI_MODEL)
        response = model.invoke(messages)
        
        return response.content
    
    except Exception as e:
        raise e
    
def send_message(
        recipient,
        text,
        sender_name,
        attachments=None,
        timeout=None,
        passthrough=None,
        status_callback=None,
        status_callback_header=None,
        reply_to_id=None,
        subject=None,
        effect=None,
        service="imessage",
    ):
    sqs_client = boto3.client("sqs")
    queue_name = SQS_NAME
    if not queue_name:
        raise ValueError("sending_loop_sqs_queue_name environment variable is not set")
    queue_url = sqs_client.get_queue_url(QueueName=queue_name).get("QueueUrl")
    if not queue_url:
        raise ValueError("SQS_QUEUE_URL environment variable is not set")
    payload = {
        "recipient": recipient,
        "text": text,
        "sender_name": sender_name,
        "attachments": attachments,
        "timeout": timeout,
        "passthrough": passthrough,
        "status_callback": status_callback,
        "status_callback_header": status_callback_header,
        "reply_to_id": reply_to_id,
        "subject": subject,
        "effect": effect,
        "service": service
    }
    try:
        print(f"Sending message to SQS: {payload}")
        sent_message = sqs_client.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(payload),
        )
    except Exception as e:
        raise e
    
def is_url(url_string):
    try:
        result = urlparse(url_string)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False
    
def transfer_image_to_s3(firebase_url: str, bucket_name: str) -> str:
    # Download image from Firebase
    try:
            response = requests.get(firebase_url)
            response.raise_for_status()

    except requests.exceptions.RequestException as e:
        print(f"Failed to download image: {e}")
        return ""

    image_bytes = BytesIO(response.content)
    image_data = image_bytes.getvalue()
    s3_key_unique = hashlib.new(algo, image_data).hexdigest()[:8]
    

    # Upload to S3
    s3 = boto3.client('s3')
    s3.upload_fileobj(image_bytes, bucket_name, s3_key_unique)

    # Construct the S3 URL (public URL if bucket/object is public)
    s3_url = f"https://{bucket_name}.s3.amazonaws.com/{s3_key_unique}"
    return s3_url

def message_inbound(payload):        
        recipient = payload.get('recipient')
        sender_name = payload.get('sender_name', 'Loop Message Sender')
        formatted_request = format_human_request(payload)
        if is_url(formatted_request['text']):
            formatted_request['text'] = transfer_image_to_s3(formatted_request['text'], formatted_request['phone'])
        write_to_chat(formatted_request=formatted_request)
        chat = gather_context(formatted_request)
        formatted_request['text'] = invoke_model(chat)
        formatted_request['human'] = False
        write_to_chat(formatted_request=formatted_request)
        
        send_message(
            recipient=recipient,
            text=formatted_request['text'],
            sender_name=sender_name,
        )
        
        
def process_webhook(payload):
    try:
        alert_type = payload.get('alert_type', 'unknown')
        
        if alert_type == "message_inbound":
            message_inbound(payload)
            
        return {
            "status": "success",
            "message": f"Message processed successfully for {alert_type}"
        }
    
    except Exception as e:
        raise e
    
    
def lambda_handler(event, context):
    try:
        success = True
        # For SQS triggered Lambda
        if 'Records' in event and len(event['Records']) > 0:
            # This is an SQS event
            for record in event['Records']:
                payload = json.loads(record['body'])
                response = process_webhook(payload)
                
        # API Gateway triggered Lambda
        elif 'body' in event:
            payload = json.loads(event['body'])
            response = process_webhook(payload)
        else:
            raise ValueError("Invalid event format")
    
    except Exception as e:
        raise e
    
    return {
        "status_code": 200,
        "response": {
            "success": success,
            "message": "Webhook processed successfully"
        }
    }

if __name__ == "__main__":
    test_event = {
        "Records": [
            {
                "body": json.dumps({
                "alert_type": "message_inbound",
                "recipient": os.environ.get("PHONE_NUMBER"),
                "text": "Hello, how are you?",
                "message_type": "text",
                "message_id": "59c55Ce8-41d6-43Cc-9116-8cfb2e696D7b",
                "webhook_id": "ab5Ae733-cCFc-4025-9987-7279b26bE71b",
                "api_version": "1.0"
            })
            }
        ]
    }
    response = lambda_handler(test_event, None)
    print(response)

