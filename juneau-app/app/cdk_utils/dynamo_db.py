from aws_cdk import aws_dynamodb as dynamodb
from constructs import Construct

class DynamoDBTable(Construct):
    def __init__(self, scope: Construct, id: str, table_name: str, **kwargs) -> None:
        super().__init__(scope, id)

        self.table = dynamodb.Table(
            self,
            f"{id}_Table",
            table_name=table_name,
            partition_key=dynamodb.Attribute(
                name="id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST
        )
