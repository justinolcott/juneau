# Loop Message App

This project provides a Python application for sending messages via the iMessage Conversation API. It includes functionalities for sending individual messages, group messages, audio messages, and reactions.

## Project Structure

```
loop-message-app
├── sending_server.py       # Main logic for sending messages
├── Dockerfile              # Instructions to build the Docker image
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables
└── README.md               # Project documentation
```

## Setup Instructions

1. **Clone the repository:**
   ```
   git clone <repository-url>
   cd loop-message-app
   ```

2. **Create a `.env` file:**
   Populate the `.env` file with the necessary environment variables:
   ```
   LOOP_API_KEY=<your_loop_api_key>
   LOOP_AUTH_KEY=<your_loop_auth_key>
   PHONE_NUMBER=<your_phone_number>
   IMESSAGE_SENDER_NAME=<your_sender_name>
   ```

3. **Install dependencies:**
   You can install the required Python packages using pip:
   ```
   pip install -r requirements.txt
   ```

## Running the Application

### Using Docker

1. **Build the Docker image:**
   ```
   docker build -t loop-message-app .
   ```

2. **Run the Docker container:**
   ```
   docker run --env-file .env loop-message-app
   ```

### Directly with Python

You can also run the application directly using Python:
```
python sending_server.py
```

## Usage Examples

To send a message, you can call the `send_message` function from `sending_server.py` with the appropriate parameters.

```python
response = send_message(
    recipient=PHONE_NUMBER,
    text="Hello from Loop Message!",
    sender_name="Loop Message Sender",
)
print(response)
```

## License

This project is licensed under the MIT License.