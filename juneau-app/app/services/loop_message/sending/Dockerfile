# FROM python:3.12-slim

# # Set the working directory
# WORKDIR /app

# # Copy the requirements file
# COPY requirements.txt .

# # Install the dependencies
# RUN pip install --no-cache-dir -r requirements.txt

# # Copy the rest of the application code
# COPY ./send_loop_message.py .

# # Command to run the application
# CMD ["python", "send_loop_message.py"]

# Instructions to build and run the Docker image
# 1. Build the Docker image
# docker build -t send_loop_message ./app/services/loop_message/send_loop_message
# 2. Run the Docker container
# docker run --rm --env-file ./app/.env send_loop_message


FROM public.ecr.aws/lambda/python:3.12

COPY send_loop_message.py requirements.txt ./

RUN python3.12 -m pip install -r requirements.txt -t .

# Command can be overwritten by providing a different command in the template directly.
CMD ["send_loop_message.lambda_handler"]
