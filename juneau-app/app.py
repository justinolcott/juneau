#!/usr/bin/env python3

import aws_cdk as cdk

from app.juneau_app_stack import JuneauAppStack
from ops.juneau_pipeline_stack import JuneauPipelineStack

from dotenv import load_dotenv
import os

load_dotenv(".env.development")

app = cdk.App()

JuneauAppStack(app, "JuneauAppStack", environment="development", env=cdk.Environment(
    account=os.getenv("AWS_ACCOUNT_ID"),
    region=os.getenv("AWS_REGION")
))

app.synth()
