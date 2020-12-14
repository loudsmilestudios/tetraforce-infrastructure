import os, logging, boto3, json, botocore.exceptions

if __name__ != "__main__":
    from aws_xray_sdk.core import xray_recorder
    from aws_xray_sdk.core import patch_all
    patch_all()

logger = logging.getLogger()
logger.setLevel(logging.INFO)

cognito = boto3.client('cognito-idp')

def lambda_handler(event, context):

    if "queryStringParameters" in event:

        # Intialize variables
        origin = None
        params = event["queryStringParameters"]

        # Validate properties
        for prop in ["username", "password"]:
            if not prop in params:
                return build_response("Missing required parameters!", False)

        
        
        # Check for request IP in headers
        if "headers" in event and "x-forwarded-for" in event["headers"]:
            origin = event["headers"]["x-forwarded-for"]
        else:
            return build_response("Request missing header! #100", False)


        # Attempt to create user
        return login_user(params["username"], params["password"], origin)
            

    return unknown_error_response()

def login_user(username, password, ip_address):
    try:
        COGNITO_USERPOOL_ID = os.environ.get("COGNITO_USERPOOL")
        COGNITO_CLIENT_ID = os.environ.get("COGNITO_CLIENT")

        loginResponse = cognito.admin_initiate_auth(
            UserPoolId = COGNITO_USERPOOL_ID,
            ClientId = COGNITO_CLIENT_ID,
            AuthFlow = "ADMIN_NO_SRP_AUTH",
            AuthParameters =
            {
                "USERNAME" : username,
                "PASSWORD" : password
            }
        )
        response = loginResponse["AuthenticationResult"]
        response["success"] = True
        response["message"] = "Successfully authenticated!"
        return response
    except Exception as e:
        return build_response(str(e), False)

def unknown_error_response():
    return build_response("An unknown error occured!", False)
    
def build_response(message, success = False):
    return {"message" : message, "success" : success}

# CLI for testing lambda
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Register user into cognito userpool")
    parser.add_argument('-u','--username', required=True, help="New user's username", dest="username")
    parser.add_argument('-p','--password', required=True, help="New user's password", dest="password")
    parser.add_argument('-c','--client-id', required=False, help="Cognito User Pool's Client ID, can be passed manually or via environment variable `COGNITO_CLIENT`", dest="client_id")
    parser.add_argument('-po', '--pool', required=False, help="Cognito User Pool's ID, can be passed manually or via environment variable", dest="pool_id")

    args = parser.parse_args()

    event = {
            'queryStringParameters':{
                "username" : args.username,
                "password" : args.password
            },
            "headers": {
                "x-forwarded-for" : "127.0.0.1"
            }
        }
    if args.pool_id:
        os.environ["COGNITO_USERPOOL"] = args.pool_id
    else:
        if not "COGNITO_USERPOOL" in os.environ:
            raise Exception("Cognito user pool must be passed via cli or environment variable!")

    if args.client_id:
        os.environ["COGNITO_CLIENT"] = args.client_id
    else:
        if not "COGNITO_CLIENT" in os.environ:
            raise Exception("Cognito client must be passed via cli or environment variable!")

    print(lambda_handler(event,{}))