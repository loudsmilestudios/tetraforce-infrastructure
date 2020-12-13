import os, logging, boto3, json, botocore.exceptions

if __name__ != "__main__":
    from aws_xray_sdk.core import xray_recorder
    from aws_xray_sdk.core import patch_all
    patch_all()

logger = logging.getLogger()
logger.setLevel(logging.INFO)

cognito = boto3.client('cognito-idp')

COGNITO_CLIENT_ID = os.environ.get("COGNITO_CLIENT")


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
        return create_user(params["username"], params["params"],
                    params["email"], origin)
            

    return unknown_error_response()

def create_user(username, password, email, ip_address):
    try:
        signUpResponse = cognito.sign_up(
            ClientId=COGNITO_CLIENT_ID,
            Username=username,
            Password=password,
            UserAttributes=[
                {
                    'Name': 'email',
                    'Value': email
                },
                {
                    'Name': 'preferred_username',
                    'Value': username
                },
                {
                    'Name': 'skin',
                    'Value': 'chain'
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
            return build_response("New user created sucessfully!", True)
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