import os
from dotenv import load_dotenv

from constructs import Construct
from aws_cdk import (
    Duration,
    Stack,
    aws_iam as iam,
    aws_sqs as sqs,
    aws_sns as sns,
    aws_sns_subscriptions as subs,
    aws_apigatewayv2_integrations as apigatewav2_integrations,
    aws_apigatewayv2 as apigatewav2,
    aws_lambda_event_sources as lambda_event_sources,
    aws_lambda as _lambda,
    aws_secretsmanager as secretsmanager,
)

from aws_cdk.aws_lambda_python_alpha import PythonFunction

from app.cdk_utils.sqs import SQS
from app.cdk_utils.dynamo_db import DynamoDBTable
from app.cdk_utils.api_gateway import APIGateway
from app.cdk_utils.route53_api_gateway import Route53APIGateway

class JuneauAppStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, environment: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # ENVIRONMENT
        """
        "Developer Specific variables like DOMAIN_NAME, AWS_ACCOUNT_ID, AWS_REGION, etc. get from a dotenv file
        "Sensitive variables like API Keys are saved in AWS Secrets Manager and referenced by a _NAME
        "Non-sensitive variables are saved in cdk.json and referenced by env_context 
        
        """
        if environment == "development":
            load_dotenv(".env.development")
        elif environment == "production":
            load_dotenv(".env.production")
        else:
            raise ValueError(f"Unknown environment: {environment}")
        self.context = self.node.try_get_context(environment)
        
        self.LOOP_BEARER_TOKEN = os.environ.get("LOOP_BEARER_TOKEN")
        if not self.LOOP_BEARER_TOKEN:
            raise ValueError("Missing environment variable: LOOP_BEARER_TOKEN")

        self.GEMINI_SECRET_NAME = self.context.get("GEMINI_SECRET_NAME")
        if not self.GEMINI_SECRET_NAME:
            raise KeyError("Missing context value: GEMINI_SECRET_NAME")

        self.LOOP_SECRET_NAME = self.context.get("LOOP_SECRET_NAME")
        if not self.LOOP_SECRET_NAME:
            raise KeyError("Missing context value: LOOP_SECRET_NAME")
        

        self.PROCESSING_SQS_NAME = self.context.get("PROCESSING_SQS_NAME", None)
        self.SENDING_LOOP_SQS_NAME = self.context.get("SENDING_LOOP_SQS_NAME", None)
        
        self.DOMAIN_NAME = os.environ.get("DOMAIN_NAME", None)
        self.SUBDOMAIN_NAME = os.environ.get("SUBDOMAIN_NAME", None)
        self.ACM_CERTIFICATE_ARN = os.environ.get("ACM_CERTIFICATE_ARN", None)
        
        
        # API GATEWAY
        self.api = None
        if self.DOMAIN_NAME is None:
            self.api = APIGateway(
                self, "APIGateway", api_name="Loop API", api_description="Webhook API for Loop"
            )
        else:
            print("Using Route 53")
            self.api = Route53APIGateway(
                self, "Route53APIGateway", api_name="Loop API", api_description="Webhook API for Loop",
                domain_name=self.DOMAIN_NAME,
                subdomain_name=self.SUBDOMAIN_NAME,
                arn=self.ACM_CERTIFICATE_ARN,
            )
        
        # DYNAMO DATABASE
        self.dynamodb_table = DynamoDBTable(self, "MyDynamoDB", table_name="MyTable")

        # RECEIVE LOOP MESSAGE LAMBDA
        self.receive_loop_message_lambda = _lambda.DockerImageFunction(
            self,
            "ReceiveLoopMessageFunction",
            code=_lambda.DockerImageCode.from_image_asset(
                "./app/services/loop_message/receiving"
            ),
            
            memory_size=128,  # smallest available
            timeout=Duration.seconds(20),
            environment={
                "ENVIRONMENT": environment,
                "SQS_NAME": self.PROCESSING_SQS_NAME,
                "LOOP_BEARER_TOKEN": self.LOOP_BEARER_TOKEN,
            },
            reserved_concurrent_executions=5,
            architecture=_lambda.Architecture.ARM_64,
        )
        
        self.receive_loop_message_lambda_integration = apigatewav2_integrations.HttpLambdaIntegration(
            "LoopWebhookIntegration",
            self.receive_loop_message_lambda
        )
        
        self.api.api.add_routes(
            path="/loop",
            methods=[apigatewav2.HttpMethod.POST],
            integration=self.receive_loop_message_lambda_integration,
        )
        
        self.api.api.add_routes(
            path="/",
            methods=[apigatewav2.HttpMethod.GET],
            integration=self.receive_loop_message_lambda_integration,
        )
        
        # PROCESSING SQS
        self.processing_message_queue = sqs.Queue(
            self,
            "ProcessingMessageQueue",
            queue_name=self.PROCESSING_SQS_NAME,
            retention_period=Duration.days(4),
            visibility_timeout=Duration.minutes(5),
        )
        
        self.processing_message_queue.grant_send_messages(
            self.receive_loop_message_lambda
        )
        
        # PROCESSING LAMBDA
        self.gemini_secret = secretsmanager.Secret.from_secret_name_v2(
            self,
            "GeminiSecret",
            secret_name=self.GEMINI_SECRET_NAME,
        )
        
        self.processing_message_lambda = PythonFunction(
            self,
            "ProcessingMessageFunction",
            entry="./app/services/processing",
            runtime=_lambda.Runtime.PYTHON_3_12,
            index="lambda.py",
            handler="lambda_handler",
            memory_size=128,
            timeout=Duration.seconds(60),
            environment={
                "ENVIRONMENT": environment,
                "SQS_NAME": self.SENDING_LOOP_SQS_NAME,
                "GEMINI_SECRET_NAME": self.GEMINI_SECRET_NAME,
            },
            reserved_concurrent_executions=5,
            architecture=_lambda.Architecture.ARM_64,
        )
        
        self.gemini_secret.grant_read(self.processing_message_lambda)
        
        self.processing_message_queue.grant_consume_messages(
            self.processing_message_lambda
        )
        
        self.processing_message_lambda.add_event_source(
            lambda_event_sources.SqsEventSource(
                self.processing_message_queue,
                batch_size=5,
            )
        )
        
        # SENDING SQS
        self.sending_loop_message_queue = sqs.Queue(
            self,
            "SendingLoopMessageQueue",
            queue_name=self.SENDING_LOOP_SQS_NAME,
            retention_period=Duration.days(4),
            visibility_timeout=Duration.minutes(5),
        )
        
        self.sending_loop_message_queue.grant_send_messages(
            self.processing_message_lambda
        )
        
        # SENDING LAMBDA
        self.loop_secret = secretsmanager.Secret.from_secret_name_v2(
            self,
            "LoopSecret",
            secret_name=self.LOOP_SECRET_NAME,
        )
        
        self.sending_loop_message_lambda = PythonFunction(
            self,
            "SendLoopMessageFunction",
            entry="./app/services/loop_message/sending",
            runtime=_lambda.Runtime.PYTHON_3_12,
            index="lambda.py",
            handler="lambda_handler",
            memory_size=128,
            timeout=Duration.second(20),
            environment={
                "ENVIRONMENT": environment,
                "LOOP_SECRET_NAME": self.LOOP_SECRET_NAME,
            },
            reserved_concurrent_executions=5,
            architecture=_lambda.Architecture.ARM_64,
        )
        
        self.loop_secret.grant_read(self.sending_loop_message_lambda)
        
        self.sending_loop_message_queue.grant_consume_messages(
            self.sending_loop_message_lambda
        )
        
        self.sending_loop_message_lambda.add_event_source(
            lambda_event_sources.SqsEventSource(
                self.sending_loop_message_queue,
                batch_size=5,
            )
        )
        