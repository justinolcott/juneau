import boto3
import json
import os

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI


GEMINI_MODEL = "gemini-2.0-flash"
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

def gather_context(incoming_data):
    number_id = incoming_data['Response']['Recipient']  # Put actual keys here based on how `incoming_data` is actually structured.
    chat_id = 1  # set to `1` for now; regex to be included and search for `✨` at the start of messages to start new chat.

    if new_chat:
        pass
        # table_to_write to = new_table

    # Write new content to table; 

    # Gather all context from table
    db_client = boto3.client('dynamodb')
    response = db_client.get_item(
        TableName='UserConversations',
        Key={
            'phone': {  # partition key
                'N': number_id,
            },
            'chat_id': {  # sort key
                'N': chat_id,
            },
        }
        ## Format table entry into message
        # ...
    )

    return response

model = ChatGoogleGenerativeAI(model=GEMINI_MODEL)

def invoke_model(payload, ):
    try:
        text = payload.get('text')
        
        messages = []
        messages.append(HumanMessage(content=text))
        response = model.invoke(messages)
        
        return response
    
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
    

def message_inbound(payload):        
        recipient = payload.get('recipient')
        sender_name = payload.get('sender_name', 'Loop Message Sender')
        
        ai_response = invoke_model(payload)
        
        send_message(
            recipient=recipient,
            text=ai_response.content,
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

