


from constructs import Construct
from aws_cdk import (
    aws_sqs as sqs,
    Duration,
    aws_lambda as _lambda,
    aws_lambda_event_sources as lambda_event_sources,
)
        
class SQS(Construct):
    def __init__(self, 
                 scope: Construct, 
                 id: str,
                 queue_id: str,
                 queue_name: str,
                 input_lambda: _lambda.IFunction, 
                 output_lambda: _lambda.IFunction,
                 retention_period: Duration = Duration.days(4),
                 visibility_timeout: Duration = Duration.minutes(5),
                 batch_size: int = 5,
                 env_context=None, 
                 **kwargs) -> None:
        super().__init__(scope, id)
        print("Init: SQS")
        
        self.queue = sqs.Queue(
            self,
            queue_id,
            queue_name=queue_name,
            retention_period=retention_period,
            visibility_timeout=visibility_timeout,
        )
        
        # Lambda Permissions
        self.queue.grant_send_messages(input_lambda)
        self.queue.grant_consume_messages(output_lambda)
        
        output_lambda.add_event_source(
            lambda_event_sources.SqsEventSource(
                self.queue,
                batch_size=batch_size,
            )
        )