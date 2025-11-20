#!/usr/bin/env python3
import os
import warnings

from aws_cdk import App, Environment, Tags
from stacks.todo_stack import TodoStack

warnings.filterwarnings("ignore", category=UserWarning, module="aws_cdk")

app = App()


env = Environment(
    account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
    region=os.environ.get("CDK_DEFAULT_REGION", "us-east-1"),
)

stack = TodoStack(app, "TodoStack", env=env)
Tags.of(stack).add("Project", "TodoApp")
Tags.of(stack).add("Environment", "dev")

app.synth()
