#!/usr/bin/env python

import logging
import json
import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException, Header, Depends, status
from fastapi.responses import JSONResponse
import uvicorn
from typing import Optional, Dict, Any

# Load environment variables
load_dotenv()

BEARER = os.getenv("LOOP_BEARER")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Create FastAPI app
app = FastAPI(title="Loop Message Webhook API")

# Authentication dependency
async def verify_token(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is missing"
        )
    
    if authorization != f"Bearer {BEARER}":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid authorization token"
        )
    
    return True

# Routes
@app.get("/")
async def get_root():
    return {"message": "Webhook server is running"}

@app.post("/webhook")
async def handle_webhook(request: Request, authenticated: bool = Depends(verify_token)):
    try:
        payload = await request.json()
        logging.info(f"Received webhook: {json.dumps(payload, indent=2)}")
        
        # Extract alert type and message details
        alert_type = payload.get('alert_type', 'unknown')
        message_id = payload.get('message_id', 'unknown')
        
        # Process based on alert type
        response_data = process_webhook(alert_type, payload)
        
        return response_data
    
    except json.JSONDecodeError:
        logging.error("Failed to parse JSON payload")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        logging.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

def process_webhook(alert_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    response = {}
    
    if alert_type == "message_inbound":
        # Handle incoming message
        recipient = payload.get('recipient', '')
        text = payload.get('text', '')
        message_type = payload.get('message_type', '')
        
        logging.info(f"Received message from {recipient}: {text}")
        
        # Return typing indicator (optional)
        # response["typing"] = 3
        # response["read"] = True
        
    elif alert_type == "message_sent":
        success = payload.get('success', False)
        if success:
            logging.info(f"Message {payload.get('message_id')} was sent successfully")
        else:
            logging.warning(f"Message {payload.get('message_id')} was not delivered")
            
    elif alert_type == "message_failed":
        error_code = payload.get('error_code', 0)
        logging.error(f"Message {payload.get('message_id')} failed with error code {error_code}")
        
    elif alert_type == "message_reaction":
        reaction = payload.get('reaction', '')
        logging.info(f"Received reaction {reaction} for message {payload.get('message_id')}")
        response["read"] = True
        
    elif alert_type == "group_created":
        group = payload.get('group', {})
        logging.info(f"Added to group: {group.get('name', 'Unnamed Group')}")
        
    else:
        logging.info(f"Received {alert_type} webhook")
        
    return response

# Run the server
if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=5280)