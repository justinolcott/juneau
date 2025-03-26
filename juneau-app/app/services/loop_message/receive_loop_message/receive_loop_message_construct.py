from dotenv import load_dotenv
from constructs import Construct
from aws_cdk import (
    aws_lambda as _lambda,
    aws_apigatewayv2 as apigatewayv2,
    Duration,
    aws_apigatewayv2_integrations as apigatewayv2_integrations,
    
)

import os

load_dotenv()

class ReceiveLoopMessageLambda(Construct):
    def __init__(self, scope: Construct, id: str, env_context=None, **kwargs) -> None:
        super().__init__(scope, id)
        print("Init: ReceiveLoopMessageLambda")
        
        if env_context is None:
            env_context = "dev"
        env = scope.node.try_get_context(env_context)
        env_file = env.get("env_file")
        load_dotenv(env_file)
        
        self.api = apigatewayv2.HttpApi(
            self,
            "LoopWebhookAPI",
            api_name="LoopWebhookAPI",
            description="API for receiving Loop webhooks",
            create_default_stage=True,
            cors_preflight=apigatewayv2.CorsPreflightOptions(
                allow_origins=["*"],
                allow_methods=[apigatewayv2.CorsHttpMethod.POST,
                               apigatewayv2.CorsHttpMethod.GET],
                allow_headers=["Content-Type", "Authorization"],
                max_age=Duration.hours(1),
            ),
        )           
        
        self.receive_loop_message_lambda = _lambda.DockerImageFunction(
            self,
            "ReceiveLoopMessageFunction",
            code=_lambda.DockerImageCode.from_image_asset(
                directory="./app/services/loop_message/receive_loop_message",
            ),
            memory_size=128,
            timeout=Duration.seconds(30),
            environment={
                "LOOP_BEARER": os.environ.get("LOOP_BEARER"),
            },
            architecture=_lambda.Architecture.ARM_64,
        )
        
        self.lambda_integration = apigatewayv2_integrations.HttpLambdaIntegration(
            "ReceiveLoopMessageIntegration",
            handler=self.receive_loop_message_lambda,
        )
        
        self.api.add_routes(
            path="/loop",
            methods=[apigatewayv2.HttpMethod.POST],
            integration=self.lambda_integration,
        )
        
        self.api.add_routes(
            path="/",
            methods=[apigatewayv2.HttpMethod.GET],
            integration=self.lambda_integration,
        )
        
        
        