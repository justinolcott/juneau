from constructs import Construct
from aws_cdk import (
    aws_route53 as route53,
    aws_certificatemanager as certificatemanager,
    aws_route53_targets as targets,
    aws_apigatewayv2 as apigatewayv2,
    Duration,
)

class Route53APIGateway(Construct):
    def __init__(self, scope: Construct, id: str, api_name: str, api_description: str, domain_name: str, subdomain_name: str, arn: str, **kwargs) -> None:
        super().__init__(scope, id)
        self.domain_name = domain_name
        self.subdomain_name = subdomain_name
        
        # Route 53
        self.hosted_zone = route53.HostedZone.from_lookup(
            self,
            f"{id}_HostedZone",
            domain_name=self.domain_name,
        )
        
        # Route 53
        self.certificate = certificatemanager.Certificate.from_certificate_arn(
            self,
            f"{id}_Certificate",
            certificate_arn=arn,
        )
        
        # Route 53
        self.domain_name = apigatewayv2.DomainName(
            self,
            f"{id}_Domain",
            domain_name=f"{subdomain_name}.{domain_name}",
            certificate=self.certificate,
            security_policy=apigatewayv2.SecurityPolicy.TLS_1_2,
        )
        
        self.api = apigatewayv2.HttpApi(
            self,
            f"{id}_API",
            api_name=api_name,
            description=api_description,
            create_default_stage=False, # False if using a custom domain with Route 53
            cors_preflight=apigatewayv2.CorsPreflightOptions(
                allow_origins=["*"],
                allow_methods=[apigatewayv2.CorsHttpMethod.POST,
                               apigatewayv2.CorsHttpMethod.GET],
                allow_headers=["Content-Type", "Authorization"],
                max_age=Duration.hours(1),
            ),
        )
        
        # Route 53
        self.stage = apigatewayv2.HttpStage(
            self,
            f"{id}_Stage",
            http_api=self.api,
            stage_name="$default",
            auto_deploy=True,
            domain_mapping=apigatewayv2.DomainMappingOptions(
                domain_name=self.domain_name,
            )
        )
        
        # Route 53
        self.route53_record = route53.ARecord(
            self,
            f"{id}_ARecord",
            record_name=f"{self.subdomain_name}",
            zone=self.hosted_zone,
            target=route53.RecordTarget.from_alias(
                targets.ApiGatewayv2DomainProperties(
                    self.domain_name.regional_domain_name,
                    self.domain_name.regional_hosted_zone_id
                )
            ),
            ttl=Duration.minutes(3),
        )
        
        