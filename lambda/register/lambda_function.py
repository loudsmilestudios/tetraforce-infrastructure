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
        for prop in ["username", "password", "email"]:
            if not prop in params:
                return build_response("Missing required parameters!", False)

        
        
        # Check for request IP in headers
        if "headers" in event and "x-forwarded-for" in event["headers"]:
            origin = event["headers"]["x-forwarded-for"]
        else:
            return build_response("Request missing header! #100", False)


        # Attempt to create user
        return create_user(params["username"], params["password"],
                    params["email"], origin)
            

    return unknown_error_response()

def create_user(username, password, email, ip_address):
    try:
        COGNITO_CLIENT_ID = os.environ.get("COGNITO_CLIENT")

        signUpResponse = cognito.sign_up(
            ClientId=COGNITO_CLIENT_ID,
            Username=username,
            Password=password,
            UserAttributes=[
                {
                    'Name': 'email',
                    'Value': email
                }
            ],
            UserContextData={
                'EncodedData': ip_address
            },
            # ClientMetadata={
            #     "CreatedByApi": "True"
            # }
        )

        # Validate response object
        if "UserConfirmed" in signUpResponse:
            logger.info(f"Registered new user: {username} as {signUpResponse['UserSub']}")
            return build_response("New user created sucessfully! Please check your email to verify your account!", True)
        else:
            logger.error(f"Malformed signup response! {json.dumps(signUpResponse)}")
            return build_response("Malformed signup response!", False)

    # Return any errors thrown by the create users request
    except botocore.exceptions.ClientError as e:
        logger.info(f"Exception occured when trying to sign up {username}: {e}")
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
    parser.add_argument('-e','--email', required=True, help="New user's email", dest="email")
    parser.add_argument('-c','--client-id', required=False, help="Cognito User Pool's Client ID, can be passed manually or via environment variable `COGNITO_CLIENT`", dest="client_id")

    args = parser.parse_args()

    event = {
            'queryStringParameters':{
                "username" : args.username,
                "password" : args.password,
                "email" : args.email,
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