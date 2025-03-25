

# Instructions

## ngrok
- https://ngrok.com/downloads/python
- Make an account and get your auth token
- In a new terminal window, just continually port with `ngrok http 5000`
- Copy the forwarding link

## Loop Message
- Make an account on loopmessage
- Copy the webhook URL from ngrok and paste it into the sandbox webhook
  - maybe add a `/loop` to the end of the URL or whatever we decide on
- Add in `BEARER WHATEVER YOU WANT HERE` to the header
- Copy the Sandbox deep link and send a message to it from your phone
- Add your phone number to the recipient list (+1 555 555 5555)
- Copy the Authorization key and secret api key

## Environment Variables
- Create a `.env` file in the root directory
- Make sure to have a .gitignore with the .env file in it
- Add the following variables to the .env file
```bash
LOOP_API_KEY=
LOOP_AUTH_KEY=
NGROK_AUTHTOKEN=
PHONE_NUMBER=
LOOP_BEARER=
ANTHROPIC_API_KEY=
```