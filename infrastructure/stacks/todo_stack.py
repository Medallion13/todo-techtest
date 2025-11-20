from aws_cdk import (
    RemovalPolicy,
    Stack,
    aws_dynamodb as dynamodb,
)
from constructs import Construct


class TodoStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope=scope, id=id, **kwargs)

        # Dynamo DB table definition

        table = dynamodb.Table(
            self,
            "TodoTable",
            table_name="TodoTable",
            # partition key
            partition_key=dynamodb.Attribute(name="PK", type=dynamodb.AttributeType.STRING),
            # Sort key para queries
            sort_key=dynamodb.Attribute(name="SK", type=dynamodb.AttributeType.STRING),
            # Billing mode: pagar solo por uso ideal para el mvp, para un produccion revisar en funcion del uso
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            # Destroy para MVP revisar para produccion
            removal_policy=RemovalPolicy.DESTROY,
        )

        self.table = table
