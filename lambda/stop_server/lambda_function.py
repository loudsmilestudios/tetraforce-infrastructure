import os, logging, boto3, json

if __name__ != "__main__":
    from aws_xray_sdk.core import xray_recorder
    from aws_xray_sdk.core import patch_all
    patch_all()

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ecs = boto3.client('ecs')

def lambda_handler(event, context):
    
    if not 'queryStringParameters' in event or not 'server' in event['queryStringParameters']:
        return build_response("Stop task requires 'server' parameter!", False)

    response = {}
    
    response = ecs.stop_task(
        cluster=os.environ.get("CLUSTER"),
        task=event['queryStringParameters']['server'],
        reason="Requested stop from public API endpoint"
    )
    
    if 'task' in response:
    
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