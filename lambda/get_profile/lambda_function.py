import os, logging, boto3, json, botocore.exceptions

if __name__ != "__main__":
    from aws_xray_sdk.core import xray_recorder
    from aws_xray_sdk.core import patch_all
    patch_all()

logger = logging.getLogger()
logger.setLevel(logging.INFO)

cognito = boto3.client('cognito-idp')

def lambda_handler(event, context):

    try:
        user = cognito.get_user(AccessToken=event["headers"]["authorization"])

        attributes = {}

        for attr in user["UserAttributes"]:
            attributes[attr["Name"]] = attr["Value"]
        
        return {
            "name" : user["Username"],
            "attributes" : attributes
        }
    except Exception as e:
        logger.error(str(e))
        return unknown_error_response()

def unknown_error_response():
    return build_response("An unknown error occured!", False)
    
def build_response(message, success = False):
    return {"message" : message, "success" : success}