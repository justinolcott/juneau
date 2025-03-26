from constructs import Construct
from aws_cdk import (
    Duration,
    Stack,
    aws_iam as iam,
    aws_sqs as sqs,
    aws_sns as sns,
    aws_sns_subscriptions as subs,
)


from app.services.loop_message.send_loop_message.send_loop_message_construct import SendLoopMessageLambda
from app.services.loop_message.receive_loop_message.receive_loop_message_construct import ReceiveLoopMessageLambda

# This is the main stack and will be where I define everything for now...
class JuneauAppStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        SendLoopMessageLambda(self, "SendLoopMessageLambda", env_context="dev")
        ReceiveLoopMessageLambda(self, "ReceiveLoopMessageLambda", env_context="dev")

