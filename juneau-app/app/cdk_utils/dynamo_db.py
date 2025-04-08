"""
A module to assist w/ adding DynamoDB tables to our stack.
"""

from aws_cdk import aws_dynamodb as dynamodb
from constructs import Construct

class DynamoDBTable(Construct):
    def __init__(self, scope: Construct, id: str, table_name: str, **kwargs) -> None:
        super().__init__(scope, id)


        self.table = dynamodb.TableV2(
            scope=self,  # set table's scope to `DynamoDBTable` construct
            f"{id}_Table",
            table_name=table_name,
            partition_key=dynamodb.Attribute(
                name="id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name='',
                tpye=dynamodb.AttrinuteType.NUMBER
            )
            # billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST# might want this later

            # Set billing standards
            billing_mode=kwargs.get("billing", 
                dynamodb.Billing.on_demand(
                            max_read_request_units=25,  # 25/sec is the free tier limit
                            max_write_request_units=25  # 25/sec is the free tier limit
                ),
            )
        )
