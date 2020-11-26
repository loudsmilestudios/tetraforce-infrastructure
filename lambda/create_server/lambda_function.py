import os, logging, boto3, json

from lobby_name_generator import generate_unique_name, is_name_free

if __name__ != "__main__":
    from aws_xray_sdk.core import xray_recorder
    from aws_xray_sdk.core import patch_all
    patch_all()

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ecs = boto3.client('ecs')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ.get("SERVERLIST_TABLE"))

ec2 = boto3.resource('ec2')
vpc = ec2.Vpc(os.environ.get("VPC_ID"))

max_server_count = os.environ.get("MAX_SERVER_COUNT", 2)

def lambda_handler(event, context):
    
    server_name = ""

    # Check if server name is being passed
    if "queryStringParameters" in event and "server" in event["queryStringParameters"]:
        server_name = event["queryStringParameters"]["server"]
        if not is_name_free(server_name, table):
            return build_response("Name '" + server_name + "' is not free to use!", False)

    # Generate unique server name if not name is provided
    if server_name == "":
        server_name = generate_unique_name(table)

    # Verify that only a desired amount of servers are running
    if tasks_at_max(max_server_count):
        return build_response("Servers are at max capacity! Please contact environment admins!", False)
    
    response = {}
    
    # Attempt to start ECS task
    try:
        subnet_list = []
        for subnet in vpc.subnets.all():
            if subnet.map_public_ip_on_launch:
                subnet_list.append(subnet.subnet_id)

        response = ecs.run_task(
            cluster=os.environ.get("CLUSTER"),
            taskDefinition=os.environ.get("TASK_DEFINITION"),
            startedBy="Public Api Endpoint",
            launchType="FARGATE",
            networkConfiguration={
                "awsvpcConfiguration": {
                    "subnets": subnet_list,
                    'securityGroups': [
                        os.environ.get("TASK_SECURITY_GROUP"),
                    ],
                    "assignPublicIp": "ENABLED"
                }
            },
            tags=[
                {
                    "key": "Name",
                    "value": server_name
                },
            ],
        )
    except ecs.exceptions.InvalidParameterException as e:
        logger.error(str(e))
        return build_response("This environment has no running cloud servers to run on!", False)
    
    # Check for failures
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
        
        # Update dynamodb table
        table.put_item(
            Item={"name" : server_name,
                  "task" : task }
        )
        
        return build_response(server_name, True)
    else:
        logger.error(response)
        return unknown_error_response()


def tasks_at_max(num):
    number_of_tasks_found = 0

    # Get first list of cluser state
    ecs_response = ecs.list_tasks(
        cluster=os.environ.get("CLUSTER"),
        launchType="FARGATE"
        )

    # Update next token
    next_token = None
    if "nextToken" in ecs_response:
        next_token = ecs_response["nextToken"]

    # Get first list's number of tasks
    if "taskArns" in ecs_response:
        number_of_tasks_found = len(ecs_response["taskArns"])

    # While there are more tasks & return tasks <= desired number of tasks
    while next_token != None and number_of_tasks_found <= num:
        ecs_response = ecs.list_tasks(
            cluster=os.environ.get("CLUSTER"),
            launchType="FARGATE",
            nextToken=next_token
            )
        
        # Update next token
        if "nextToken" in ecs_response:
            next_token = ecs_response["nextToken"]
        else:
            next_token = None
        
        # Update number of tasks
        if "taskArns" in ecs_response:
            number_of_tasks_found = number_of_tasks_found + len(ecs_response["taskArns"])

    return number_of_tasks_found >= num

def unknown_error_response():
    return build_response("An unknown error occured!", False)
    
def build_response(message, success = False):
    return {"message" : message, "success" : success}