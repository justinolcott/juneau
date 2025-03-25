from aws_cdk import Stage
from constructs import Construct

from app.juneau_app_stack import JuneauAppStack

# Define the stage
class JuneauStage(Stage):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        
        JuneauAppStack(self, "JuneauAppStack")