import os

from constructs import Construct
from aws_cdk import (
    aws_secretsmanager as secretsmanager,
    aws_lambda as _lambda,
    aws_iam as iam,
    Duration,
)

from aws_cdk.aws_lambda_python_alpha import PythonFunction

class SendLoopMessageLambda(Construct):
    def __init__(self, scope: Construct, id: str, env_context=None, **kwargs) -> None:
        super().__init__(scope, id)
        print("Init: SendLoopMessageLambda")
        
        # Environment Setup
        if env_context is None:
            env_context = "dev"
        env = scope.node.try_get_context(env_context)
        loop_secret_name = env.get("loop_secret_name")
        loop_secret = secretsmanager.Secret.from_secret_name_v2(
            self,
            "LoopSecret",
            loop_secret_name,
        )
        
        # Lambda
        self.message_lambda = PythonFunction(
            self,
            "SendLoopMessageFunction",
            entry="./app/services/loop_message/send_loop_message",
            runtime=_lambda.Runtime.PYTHON_3_12,
            index="send_loop_message.py",
            handler="lambda_handler",
            memory_size=128,
            timeout=Duration.seconds(30),
            environment={
                "environment": env_context,
                "loop_secret_name": loop_secret.secret_name,
            },
            reserved_concurrent_executions=5,
        )

        loop_secret.grant_read(self.message_lambda)
