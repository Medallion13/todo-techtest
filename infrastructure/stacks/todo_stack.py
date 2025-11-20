from pathlib import Path

from aws_cdk import (
    CfnOutput,
    Duration,
    RemovalPolicy,
    Stack,
    aws_apigateway as apigateway,
    aws_cognito as cognito,
    aws_dynamodb as dynamodb,
    aws_lambda as lambda_,
)
from constructs import Construct

# ARN de la Layer pública de Powertools para Python 3.12
# Ref: https://docs.powertools.aws.dev/lambda/python/latest/#lambda-layer
POWERTOOLS_LAYER_ARN = "arn:aws:lambda:us-east-1:017000801446:layer:AWSLambdaPowertoolsPythonV2:78"


class TodoStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope=scope, id=id, **kwargs)

        # ========================================================================================================
        # DynamoDB Table

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

        # ========================================================================================================
        # Cognito User Pool

        user_pool = cognito.UserPool(
            self,
            "TodoUserPool",
            user_pool_name="TodoUsers",
            # autoregistro
            self_sign_up_enabled=True,
            # Login con email
            sign_in_aliases=cognito.SignInAliases(email=True, username=False),
            # Verificacion automatica para el MVP
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            # valores requeridos
            standard_attributes=cognito.StandardAttributes(
                email=cognito.StandardAttribute(
                    required=True,
                    mutable=True,  # se podra actualizar
                )
            ),
            # politica de contraseñas
            password_policy=cognito.PasswordPolicy(
                min_length=8,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=False,  # simplificar testing
            ),
            # Destruir ante eliminacion para MVP revisar para prod
            removal_policy=RemovalPolicy.DESTROY,
        )

        self.user_pool = user_pool

        # ========================================================================================================
        # User Pool Client (para el front)

        user_pool_client = user_pool.add_client(
            "TodoAppClient",
            # Nombre del cliente
            user_pool_client_name="TodoWebApp",
            # Auth flows permitidos
            auth_flows=cognito.AuthFlow(
                user_password=True,  # Usuario + contraseña
                user_srp=True,  # Secure Remote Password (más seguro)
                admin_user_password=True,
            ),
            # NO generar client secret (SPAs no pueden mantenerlo secreto)
            generate_secret=False,
            prevent_user_existence_errors=True,
        )

        self.user_pool_client = user_pool_client

        # ========================================================================================================
        # API GATEWAY - REST API
        api = apigateway.RestApi(
            self,
            "TodoApi",
            rest_api_name="Todo API",
            description="API for To-Do app",
            # default cors configuration
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=["http://localhost:5173"],  # future vite dev server deployment
                allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                allow_headers=[
                    "Content-Type",
                    "Authorization",
                    "X-Amz-Date",
                    "X-Api-Key",
                    "X-Amz-Security-Token",
                ],
                allow_credentials=True,
            ),
        )

        self.api = api

        # ========================================================================================================
        # Cognito authoraizer
        authoraizer = apigateway.CognitoUserPoolsAuthorizer(
            self,
            "TodoAuthoraizer",
            cognito_user_pools=[self.user_pool],
            authorizer_name="CognitoAuthorizer",
            identity_source="method.request.header.Authorization",
        )

        self.authoraizer = authoraizer

        task_resource = self.api.root.add_resource("tasks")

        # ========================================================================================================
        # Task Lambdas Function (with bundled dependencies)

        # create
        bundle_path = Path(__file__).parent.parent.parent / ".build" / "bundle"

        powertools_layer = lambda_.LayerVersion.from_layer_version_arn(
            self,
            "PowertoolsLayer",  # ← Solo se crea UNA vez aquí
            POWERTOOLS_LAYER_ARN,
        )

        create_task_fn = lambda_.Function(
            self,
            "CreateTaskFunction",
            function_name="todo-create-task",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="functions.tasks.create.handler",
            code=lambda_.Code.from_asset(str(bundle_path)),
            layers=[powertools_layer],
            environment={
                "TABLE_NAME": table.table_name,
                "POWERTOOLS_SERVICE_NAME": "todo-api",
                "LOG_LEVEL": "INFO",
            },
            timeout=Duration.seconds(10),
            memory_size=256,
        )

        # Grant DynamoDB permissions
        table.grant_read_write_data(create_task_fn)

        # API Integration
        task_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(create_task_fn),  # type: ignore
            authorizer=self.authoraizer,
        )

        # List task
        list_tasks_fn = lambda_.Function(
            self,
            "ListTasksFunction",
            function_name="todo-list-tasks",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="functions.tasks.list.handler",
            code=lambda_.Code.from_asset(str(bundle_path)),
            layers=[powertools_layer],
            environment={
                "TABLE_NAME": table.table_name,
                "POWERTOOLS_SERVICE_NAME": "todo-api",
                "LOG_LEVEL": "INFO",
            },
            timeout=Duration.seconds(10),
            memory_size=256,
        )

        table.grant_read_data(list_tasks_fn)

        # API Integration
        task_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(list_tasks_fn),  # type: ignore
            authorizer=self.authoraizer,
        )

        # ========================================================================================================
        # auth Lambda Functions (with bundled dependencies)

        # register lambda
        register_fn = lambda_.Function(
            self,
            "RegisterFunction",
            function_name="todo-register",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="functions.auth.register.handler",
            code=lambda_.Code.from_asset(str(bundle_path)),
            layers=[powertools_layer],
            environment={
                "USER_POOL_ID": user_pool.user_pool_id,
                "POWERTOOLS_SERVICE_NAME": "todo-api",
                "LOG_LEVEL": "INFO",
            },
            timeout=Duration.seconds(10),
            memory_size=256,
        )

        user_pool.grant(register_fn, "cognito-idp:AdminCreateUser", "cognito-idp:AdminSetUserPassword")

        # Lambda Login
        login_fn = lambda_.Function(
            self,
            "LoginFunction",
            function_name="todo-login",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="functions.auth.login.handler",
            code=lambda_.Code.from_asset(str(bundle_path)),
            layers=[powertools_layer],
            environment={
                "USER_POOL_CLIENT_ID": user_pool_client.user_pool_client_id,
                "POWERTOOLS_SERVICE_NAME": "todo-api",
                "LOG_LEVEL": "INFO",
            },
            timeout=Duration.seconds(10),
            memory_size=256,
        )

        user_pool.grant(login_fn, "cognito-idp:InitiateAuth")

        # ========================================================================================================
        # auth resource
        auth_resource = self.api.root.add_resource("auth")

        # ========================================================================================================
        # Auth endpoints

        register_resource = auth_resource.add_resource("register")
        register_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(register_fn),  # type: ignore
        )

        login_resource = auth_resource.add_resource("login")
        login_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(login_fn),  # type: ignore
        )

        # ========================================================================================================
        # Output for env and front

        CfnOutput(
            self,
            "UserPoolId",
            value=self.user_pool.user_pool_id,
            description="Cognito User Pool ID",
            export_name="TodoUserPoolId",
        )

        CfnOutput(
            self,
            "UserPoolClientId",
            value=self.user_pool_client.user_pool_client_id,
            description="Cognito User Pool Client ID",
            export_name="TodoUserPoolClientId",
        )

        CfnOutput(
            self,
            "ApiUrl",
            value=self.api.url,
            description="API Gateway URL",
            export_name="TodoApiUrl",
        )

        CfnOutput(
            self,
            "Region",
            value=self.region,
            description="AWS Region",
            export_name="TodoRegion",
        )
