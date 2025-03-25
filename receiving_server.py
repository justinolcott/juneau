#!/usr/bin/env python

from http.server import HTTPServer, BaseHTTPRequestHandler
import logging
import json
import os
from dotenv import load_dotenv

load_dotenv()

BEARER = os.getenv("LOOP_BEARER")

class WebhookHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = bytes("Webhook server is running", "utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)
    
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            payload = json.loads(post_data)
            logging.info(f"Received webhook: {json.dumps(payload, indent=2)}")
            
            # Make sure the header Bearer is "JUSTI"
            if 'Authorization' in self.headers:
                auth_header = self.headers['Authorization']
                if auth_header == f"Bearer {BEARER}":
                    logging.info("Authorization token is valid")
                else:
                    logging.error("Authorization token is invalid")
                    self.send_response(403)
                    self.end_headers()
                    return
            
            # Extract alert type and message details
            alert_type = payload.get('alert_type', 'unknown')
            message_id = payload.get('message_id', 'unknown')
            
            # Process based on alert type
            response_data = self.process_webhook(alert_type, payload)
            
            # Send response
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            response_json = json.dumps(response_data)
            self.send_header("Content-Length", len(response_json.encode()))
            self.end_headers()
            self.wfile.write(response_json.encode())
            
        except json.JSONDecodeError:
            logging.error("Failed to parse JSON payload")
            self.send_response(400)
            self.end_headers()
        except Exception as e:
            logging.error(f"Error processing webhook: {str(e)}")
            self.send_response(500)
            self.end_headers()
    
    def process_webhook(self, alert_type, payload):
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

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Create the server
server = HTTPServer(("localhost", 5280), WebhookHandler)

try:
    logging.info("Starting webhook server on port 5280. Press Ctrl+C to stop.")
    server.serve_forever()
except KeyboardInterrupt:
    logging.info("Shutting down server...")
    server.server_close()
    logging.info("Server stopped cleanly.")