import os, logging, boto3, json

if __name__ != "__main__":
    from aws_xray_sdk.core import xray_recorder
    from aws_xray_sdk.core import patch_all
    patch_all()

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ecs = boto3.client('ecs')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ.get("SERVERLIST_TABLE"))

def lambda_handler(event, context):
    
    if not 'queryStringParameters' in event or not 'server' in event['queryStringParameters']:
        return build_response("Stop task requires 'server' parameter!", False)

    server_name = event['queryStringParameters']['server']

    aws_resp = table.get_item(
        Key={"name" : server_name}
    )
    if not 'Item' in aws_resp:
        return build_response("The server you are trying to stop does not exist", False)
    if not 'task' in aws_resp['Item']:
        return build_response("The server you are trying to stop does not have an associated task!", False)

    response = {}
    
    try:
        response = ecs.stop_task(
            cluster=os.environ.get("CLUSTER"),
            task=aws_resp['Item']['task'],
            reason="Requested stop from public API endpoint"
        )
    except ecs.exceptions.InvalidParameterException as e:
        return build_response("Tried to stop task, but was unable to find task in cluster!", False)
    
    if 'task' in response:
    
        table.delete_item(
            Key={ "name" : server_name }
        )

        task = response['task']['taskArn']
        waiter = ecs.get_waiter('tasks_stopped')
        waiter.wait(tasks=[task], cluster=os.environ.get("CLUSTER"))
        
        return build_response("Tasks have successfully stopped!", True)
    else:
        logger.error(response)
        return unknown_error_response()

def unknown_error_response():
    return build_response("An unknown error occured!", False)
    
def build_response(message, success = False):
    return {"message" : message, "success" : success}