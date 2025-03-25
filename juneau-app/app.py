#!/usr/bin/env python3

import aws_cdk as cdk

from app.juneau_app_stack import JuneauAppStack
from ops.juneau_pipeline_stack import JuneauPipelineStack

app = cdk.App()
JuneauPipelineStack(app, "JuneauPipelineStack")

app.synth()
