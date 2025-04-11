


# Setup Instructions
## Installations
- Install gh cli https://github.com/cli/cli
- Install docker https://docs.docker.com/engine/install/
    - Confirm that this works via `docker --version`
    - Install a daemon, too. If not using Linux, install a tool like _DockerDesktop_ or _Colima_
- Install AWS CLI https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html
- Install node 22, nvm, and npm/pnpm https://nodejs.org/en/download
- Install AWS CDK https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html

## Environment Setup
- `gh auth login`
- `git clone https://github.com/justinolcott/juneau.git`
- `cd juneau/juneau-app`
- `pip install uv` to install uv for speed and never use plain pip again
- `uv venv` to create a virtual environment
- `source .venv/bin/activate` to activate the virtual environment
- `uv pip install -r requirements.txt` to install dependencies
- Add keys by going to AWS Access Portal, click on your name, and then click on "Access Keys"
- Use '_Option 1: Set AWS environment variables_' in your respective os (seems to need replaced every [8 hours](https://docs.aws.amazon.com/singlesignon/latest/userguide/configure-user-session.html#:~:text=The%20default%20session%20duration%20is%208%20hours.))
- Run `cdk bootstrap` to set up the environment

## Environment Variables
- Make a `.env.development` file in the `juneau/juneau-app/` directory. Paste the following inside:
```bash
# Local development environment variables
LOOP_API_KEY=
LOOP_AUTH_KEY=

# LOOP
LOOP_BEARER_TOKEN=choose_whatever_you_want_like_your_pets_name

# GEMINI
GEMINI_API_KEY=

# ANTHROPIC
ANTHROPIC_API_KEY=optional

# AWS Secrets Manager Pointer
LOOP_SECRET_NAME=dev/juneau/loop
GEMINI_SECRET_NAME=dev/juneau/gemini

# AWS
AWS_ACCOUNT_ID=
AWS_REGION=us-east-1

# Phone Number
PHONE_NUMBER=+12345678910  # used in processing lambda

# # Route 53
# ACM_CERTIFICATE_ARN=
# DOMAIN_NAME=
```

### LOOP
- Make an account at https://loopmessage.com/
- Go to dashboard &rarr; 2-Way Conversation API &rarr; Settings
- Copy the Authorization Key and Secret API Key over to `.env.development`
- Add your phone number to the Loop account with +1 in the Sandbox Recipients field, e.g. _+12345678900_; you can also add emails.
- Copy the link and send an iMessage to the Sandbox Loop number (You can save the number in your contacts: `Juneau`)
- Under Sandbox Webhook, set a Header like 'Bearer {LOOP_BEARER}'
- After deploying, we will need to set the URL to `https://{DOMAIN_NAME}/loop` (this is the domain name you set up in Route 53 or the domain name that API Gateway gives you)

### Google Gemini
- Obtain API key from Google Gemini https://aistudio.google.com/apikey
    - If you need to make a project, do that and just don't connect a billing account
- Set the API key in the `.env.development` file


### AWS
- Go to AWS Console and create a new secret in **Secrets Manager**
- Select '_Other type of secret_' and enter the following into the key-value pairs:
    - Key: `LOOP_API_KEY`        &emsp;&emsp;Value: `<api_key>`
    - Key: `LOOP_AUTH_KEY`    &emsp;&emsp;Value: `<auth_key>`
- Next, name the secret `dev/juneau/loop` and just leave the rest as default and create the secret

- Go to AWS Console and create a new secret in **Secrets Manager**
- Select '_Other type of secret_' and enter the following into the key-value pair:
    -  Key: `GEMINI_API_KEY`   &emsp;&emsp;Value: `<api_key>`
- Next, name the secret `dev/juneau/gemini`. and just leave the rest as default and create the secret

# Deployment
- Ensure your Docker daemon is running with `docker ps`
- Run `cdk synth` to synthesize the CloudFormation template
- Run `cdk deploy` to deploy the stack
- This will create a new stack in AWS CloudFormation. We can go to the AWS Console &rarr; Lambda &rarr; Functions and look at each Lambda.
- In the `send_loop_message` Lambda, we can test it manually by clicking on the test button and entering the following event:
```json
{
  "Records": [
        {
            "body": {
                "recipient": "+18085555555",
                "text": "hi",
                "sender_name": "Juneau"
            }
        }
    ]
}
```
- In the receive_loop_message lambda, we can test it manually by going to the API Gateway and copying the link.
- You can go to the root url and see if you see a message.
- We can also set the url/loop to the webhook url in Loop Messages and test it by sending a message to the Loop Messages number and seeing if it comes through by looking at the logs in CloudWatch
- Or sending a curl request to the endpoint
```bash
curl -v -X POST "{api_gateway_url}/loop" \
     -H "Authorization: Bearer <my_name_token>" \
     -H "Content-Type: application/json" \
     -d '{
           "alert_type": "message_inbound",
           "recipient": "<my_number>",
           "text": "hello there",
           "message_type": "text",
           "api_version": "1.0", 
           "sandbox":True, 
           "message": "Hello World"
         }'
```

- Run `cdk destroy` to destroy the stack when you want



That should be it!

# Locally
- Ideally, we should be able to test things locally, so we can quickly iterate. Unfortunately, we might not be able to test communication between resources, but we can test the individual components in isolation.
- In all of our Lambdas, we should have it be runnable locally.
- Run `export environment=local`

## Sending Message
- Here, running locally is done by first setting the environment variables by using the lambda script's `load_dotenv` function.
- The function is then run with the main function
- `python app/services/loop_message/send_loop_message/send_loop_message.py +15555555555 n"Hello from Juneau!"`

## Receiving Messages
- Here, running locally is done again by first setting the environment variables by using `load_dotenv` in the lambda script.
- We then test it by running a fast api server
- `python app/services/loop_message/receive_loop_message/receive_loop_message.py`
- This provides us with a local server that we can use to receive messages, but right now it is not exposed to the internet
- We can go to the PORTS tab in VS Code and forward the port 5280, right click it and change the visibility to public, and then copy the link
- We can test this by going to the link and seeing if it works
- We can then give this {your_public_link_here}/loop to Loop Messages as the webhook URL
- This will allow us to receive messages from Loop Messages and send them to the local server
- We can then test it by sending a message to the Loop Messages number and seeing if it comes through

- Receiving messages is actually turned into a docker image, so we could test that as well by doing:
- `docker build -t juneau-loop-receive app/services/loop_message/receive_loop_message`
- `docker run -p 8000:8000 juneau-loop-receive --host 0.0.0.0 --env_file .env.development`
- This will run the docker image and expose the port 8000 to the local machine
- We can then go to the PORTS tab in VS Code and forward the port 8000, right click it and change the visibility to public, etc, etc


# Managing Secrets
## CDK Code
- In juneau_app_stack.py, we can specify the env_context variable which gets passed to the lambdas cdk code.
- When we create lambdas in the cdk code, we can use env_context and look up in cdk.json the relevant environment context.
```json
"dev": {
      "env": "development",
      "env_file": ".env.development",
      "loop_secret_name": "dev/juneau/loop"
    },
    "prod": {
      "env": "production",
      "env_file": ".env.production",
      "loop_secret_name": "dev/juneau/loop"        
    }
```
- We can then use this env_context to get the relevant environment variables to pass on to the lambdas like which secret name to use.
- We then create the lambda function and pass in the environment variables to the lambda function.

## Lambda Code
- We have an environment variable that informs the lambdas whether we are local, dev, or prod
### Locally
- If we are local, we load_dotenv and load the environment variables from the .env.development file

### Dev or Prod
- If we are dev or prod, we load the environment variables from AWS Secrets Manager
- We use the boto3 library to get the secret from AWS Secrets Manager using the secret name




# Other
## Route 53
- Go to Route 53
- Buy a domain name, it should create a new hosted zone
- Put the new domain name in the .env.development file
- Go to AWS Certificate Manager
- Request a public certificate
- Add the *.{DOMAIN_NAME} and {DOMAIN_NAME} to the certificate
- Copy the CNAME name and value
- Go to Route 53, hosted zones, and select the domain name
- Click on the domain name and create a new record set
- Select CNAME and paste the name and value from the certificate
    - Make sure not to add the domain name to the name field, it should just be the name of the certificate
- Click create
- Go back to AWS Certificate Manager and click on the certificate
- It should be resolved soon
- Copy the ARN of the certificate and paste it into the .env.development file
- Uncomment the lines in the cdk stack



# TODO
## Context
- Add a db to store conversations
- Add s3 to store files
- Add some sort of management system to manage conversations and limit context
- Add RAG maybe

## Modalities
- Add image, audio, file, and video for input
- Add image for output (and eventually audio)

## Code
- Add strong typing using pydantic to all requests and responses
- Add testing
- Add error handling

## Models
- Add different models like Gemini, Anthropic, and OpenAI

## Tools
- Add tools like Google Calendar, Gmail, Search, and more.

## Commands
- Add commands like /help or other prebuilt commands
- Add commands to switch between different models

## Other
- Send read receipts when we receive a message
- Add group message functionality
- Add scheduled messages functionality
- Add a way to use reply to messages (maybe to handle multiple conversations)
    - Replying to own message could:
        - Edit the message
    - Replying to the AI message could:
        - Continue the conversation
- Add a way to use reactions
    - User send a reaction
        - On a AI Message
            - A exclamation/heart could save it to a list.
            - A thumbs up could indicate approval for a human in the loop action.
            - A thumbs down could indicate disapproval for a human in the loop action.
            - A heart/exclamation/thumbs down could mean that the conversation is done.
            - A question mark could mean to expound upon the message.
        - On a User Message
            - A exclamation/heart could save it to a list or makes a reminder
            - A thumbs up could save it to a high priority list
            - A thumbs down could save it to a low priority list
            - A question mark could mean to retry responding to the message.
            - A heart/exclamation/thumbs down could mean that the conversation is done.
    - An AI could send a reaction (only one reaction per message at a time)
        - Could indicate which model was used
        - Could indicate if a tool was used
        - Could indicate that a task was completed
        - Could be for fun


- A subject line could be used to switch model or type of response like reasoning or deep research

### Other Other
- Could add in prompt templates, shortcuts, reminders, and more (think Raycast)
- Could add in voice calling with Vapi

    
## Frontend
- Add a frontend for signup and management
