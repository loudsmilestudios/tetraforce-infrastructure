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
        for prop in ["username"]:
            if not prop in params:
                return build_response("Missing required parameters!", False)

        
        
        # Check for request IP in headers
        if "headers" in event and "x-forwarded-for" in event["headers"]:
            origin = event["headers"]["x-forwarded-for"]
        else:
            return build_response("Request missing header! #100", False)


        # Attempt to create user
        return login_user(params["username"], origin)
            

    return unknown_error_response()

def login_user(username, ip_address):
    try:
        COGNITO_CLIENT_ID = os.environ.get("COGNITO_CLIENT")

        loginResponse = cognito.forgot_password(
            ClientId=COGNITO_CLIENT_ID,
            UserContextData={
                'EncodedData': ip_address
            },
            Username=username,
        )
        return build_response("Check your email!", True)
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
    parser.add_argument('-c','--client-id', required=False, help="Cognito User Pool's Client ID, can be passed manually or via environment variable `COGNITO_CLIENT`", dest="client_id")
    args = parser.parse_args()

    event = {
            'queryStringParameters':{
                "username" : args.username
            },
            "headers": {
                "x-forwarded-for" : "127.0.0.1"
            }
        }

    if args.client_id:
        os.environ["COGNITO_CLIENT"] = args.client_id
    else:
        if not "COGNITO_CLIENT" in os.environ:
            raise Exception("Cognito client must be passed via cli or environment variable!")

    print(lambda_handler(event,{}))