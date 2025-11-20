from aws_cdk import (
    CfnOutput,
    RemovalPolicy,
    Stack,
    aws_apigateway as apigateway,
    aws_cognito as cognito,
    aws_dynamodb as dynamodb,
)
from constructs import Construct


class TodoStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope=scope, id=id, **kwargs)

        # ========================================================================================================
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

        # ========================================================================================================
        # Cognito User Pool definition

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
            ),
            # NO generar client secret (SPAs no pueden mantenerlo secreto)
            generate_secret=False,
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
        # Cognito Authorizer for API

        authorizer = apigateway.CognitoUserPoolsAuthorizer(
            self,
            "TODOAuthorizer",
            cognito_user_pools=[self.user_pool],
            authorizer_name="CognitoAuthorizer",
            identity_source="method.request.header.Authorization",
        )

        self.authorizer = authorizer

        # ========================================================================================================
        # TODO Endpoint placeholder for first deploy

        task_resource = api.root.add_resource("tasks")

        # /get Tasks

        task_resource.add_method(
            "GET",
            apigateway.MockIntegration(
                integration_responses=[
                    apigateway.IntegrationResponse(
                        status_code="200",
                        response_templates={"application/json": '{"message": "Endpoint not implemented yet"}'},
                    )
                ],
                passthrough_behavior=apigateway.PassthroughBehavior.NEVER,
                request_templates={"application/json": '{"statusCode": 200}'},
            ),
            method_responses=[apigateway.MethodResponse(status_code="200")],
            authorizer=self.authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO,
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
