#!/usr/bin/env python3
import os
import warnings

from aws_cdk import App, Environment
from stacks.todo_stack import TodoStack

warnings.filterwarnings("ignore", category=UserWarning, module="aws_cdk")
app = App()


# Enviroment para localStack
env = Environment(
    account=os.getenv("CDK_DEFAULT_ACCOUNT", "000000000000"), region=os.getenv("CDK_DEFAULT_REGION", "us-east-1")
)

TodoStack(app, "TodoStack", env=env)

app.synth()
