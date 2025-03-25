from aws_cdk import (
    Stack,
    aws_codebuild as codebuild,
    aws_codepipeline as codepipeline,
    pipelines,
    SecretValue
)
from constructs import Construct

from ops.juneau_stage import JuneauStage

class JuneauPipelineStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)
        
        # Define source repository (GitHub, CodeCommit, etc.)
        source = pipelines.CodePipelineSource.git_hub(
            "justinolcott/juneau",  # GitHub repository
            "main",  # Branch to watch
            authentication=SecretValue.secrets_manager("github-token") # Need to set up a GitHub token in AWS Secrets Manager
        )
        
        # Define the synth step
        synth = pipelines.ShellStep("Synth",
            input=source,
            commands=[
                "pip install -r requirements.txt",
                "npm install -g aws-cdk",
                "cdk synth"
            ]
        )
        
        # Create the pipeline
        pipeline = pipelines.CodePipeline(
            self, "Pipeline",
            pipeline_name="JuneauPipeline",
            synth=synth,
            self_mutation=True  # This makes the pipeline self-updating
        )
        
        # Add application stage
        pipeline.add_stage(JuneauStage(self, "dev"))
