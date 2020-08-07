import os, logging, boto3, json

if __name__ != "__main__":
    from aws_xray_sdk.core import xray_recorder
    from aws_xray_sdk.core import patch_all
    patch_all()

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ecs = boto3.client('ecs')

def lambda_handler(event, context):
    
    response = {}
    
    try:
        response = ecs.run_task(
            cluster=os.environ.get("CLUSTER"),
            taskDefinition=os.environ.get("TASK_DEFINITION"),
            startedBy="Public Api Endpoint"
        )
    except ecs.exceptions.InvalidParameterException as e:
        return build_response("This environment has no running cloud servers to run on!", False)
    
    if 'tasks' in response:
        if 'failures' in response and len(response['failures']) > 0:
            failure = response['failures'][0]
            if 'RESOURCE' in failure['reason']:
                return build_response("No space is availible on our servers! Sorry!", False)
            else:
                logger.error(failure)
                return unknown_error_response()
    
    if len(response['tasks']) > 0:
    
        task = response['tasks'][0]['taskArn']
        waiter = ecs.get_waiter('tasks_running')
        waiter.wait(tasks=[response['tasks'][0]['taskArn']], cluster=os.environ.get("CLUSTER"))
        
        lobby = task
        
        return build_response(lobby, True)
    else:
        logger.error(response)
        return unknown_error_response()

def unknown_error_response():
    return build_response("An unknown error occured!", False)
    
def build_response(message, success = False):
    return {"message" : message, "success" : success}