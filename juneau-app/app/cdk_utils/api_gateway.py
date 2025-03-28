from constructs import Construct
from aws_cdk import (
    aws_route53 as route53,
    aws_certificatemanager as certificatemanager,
    aws_route53_targets as targets,
    aws_apigatewayv2 as apigatewayv2,
    Duration,
)

class APIGateway(Construct):
    def __init__(self, scope: Construct, id: str, api_name: str, api_description: str, **kwargs) -> None:
        super().__init__(scope, id)

        self.api = apigatewayv2.HttpApi(
            self,
            f"{id}_API",
            api_name=api_name,
            description=api_description,
            create_default_stage=True,  # False if using a custom domain with Route 53
            cors_preflight=apigatewayv2.CorsPreflightOptions(
                allow_headers=["*"],
                allow_methods=[apigatewayv2.CorsHttpMethod.ANY],
                allow_origins=["*"],
                max_age=Duration.hours(1),
            ),
        )