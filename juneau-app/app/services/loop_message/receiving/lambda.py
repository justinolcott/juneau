#!/usr/bin/env python

import boto3
import json
import logging
import os
import uvicorn

from dotenv import load_dotenv
from fastapi import FastAPI, Depends, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse
from typing import Any, Dict, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "local")
if ENVIRONMENT == "local":
    load_dotenv(".env.development")
LOOP_BEARER_TOKEN = os.getenv("LOOP_BEARER_TOKEN")
SQS_NAME = os.getenv("SQS_NAME")

# Create FastAPI app
app = FastAPI(title="Loop Message Webhook API")

def log(message: str):
    logging.info(message)

# Authentication dependency
async def verify_token(authorization: Optional[str] = Header(None)):
    logging.info(f"Authorization header: {authorization}")
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is missing"
        )
    
    if authorization != f"Bearer {LOOP_BEARER_TOKEN}":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid authorization token"
        )
    
    return True

# Routes
@app.get("/")
async def get_root():
    return {"message": "Webhook server is running"}

@app.post("/loop")
async def handle_webhook(request: Request, authenticated: bool = Depends(verify_token),):
    try:
        payload = await request.json()
        logging.info(f"Received webhook: {json.dumps(payload, indent=2)}")
        
        packaged_payload = json.dumps(payload)
        sqs_name = os.getenv("SQS_NAME")
        if not sqs_name:
            logging.error("SQS_NAME environment variable is not set")
            raise HTTPException(status_code=500, detail="SQS name not configured")
        sqs_client = boto3.client('sqs')
        queue_url = sqs_client.get_queue_url(QueueName=SQS_NAME).get('QueueUrl')
        if not queue_url:
            logging.error("SQS_QUEUE_URL environment variable is not set")
            raise HTTPException(status_code=500, detail="SQS queue URL not configured")
        try:
            sent_message = sqs_client.send_message(
                QueueUrl=queue_url,
                MessageBody=packaged_payload,
            )
                            
            logging.info(f"Message sent to SQS: {sent_message['MessageId']}")
            return JSONResponse(
                status_code=status.HTTP_200_OK, # Maybe make this a 202 Accepted
                content={
                    "status": "success",
                    "message": f"Message sent to SQS: {sent_message['MessageId']}"
                }
            )
        except Exception as e:
            logging.error(f"Error sending message to SQS: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to send message to SQS: {str(e)}")
    except json.JSONDecodeError:
        logging.error("Failed to parse JSON payload")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        logging.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# def process_webhook(alert_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
#     response = {}
    
#     if alert_type == "message_inbound":
#         # Handle incoming message
#         recipient = payload.get('recipient', '')
#         text = payload.get('text', '')
#         message_type = payload.get('message_type', '')
        
#         logging.info(f"Received message from {recipient}: {text}")
        
        
        

        
#         # Return typing indicator (optional)
#         # response["typing"] = 3
#         # response["read"] = True
        
#     elif alert_type == "message_sent":
#         success = payload.get('success', False)
#         if success:
#             logging.info(f"Message {payload.get('message_id')} was sent successfully")
#         else:
#             logging.warning(f"Message {payload.get('message_id')} was not delivered")
            
#     elif alert_type == "message_failed":
#         error_code = payload.get('error_code', 0)
#         logging.error(f"Message {payload.get('message_id')} failed with error code {error_code}")
        
#     elif alert_type == "message_reaction":
#         reaction = payload.get('reaction', '')
#         logging.info(f"Received reaction {reaction} for message {payload.get('message_id')}")
        
#     elif alert_type == "group_created":
#         group = payload.get('group', {})
#         logging.info(f"Added to group: {group.get('name', 'Unnamed Group')}")
        
#     else:
#         logging.info(f"Received {alert_type} webhook")
        
#     return response

# Only run the server directly when in local development mode
if __name__ == "__main__" and ENVIRONMENT == "local":
    uvicorn.run(app, host="localhost", port=5280)