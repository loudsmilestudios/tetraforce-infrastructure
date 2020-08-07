import os, logging, boto3, json

if __name__ != "__main__":
    from aws_xray_sdk.core import xray_recorder
    from aws_xray_sdk.core import patch_all
    patch_all()

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ecs = boto3.client('ecs')
ec2 = boto3.resource('ec2')

def lambda_handler(event, context):
    data = None
    if "queryStringParameters" in event and "server" in event["queryStringParameters"]:
        server_info = get_task_info([event["queryStringParameters"]["server"]])
        logger.info("Returning queried server: " + event["queryStringParameters"]["server"])
        data = server_info
    elif "queryStringParameters" in event and "page" in event["queryStringParameters"]:
        server_info = get_task_info(get_tasks(int(event["queryStringParameters"]["page"])))
        logger.info("Returning page: " + str(event["queryStringParameters"]["page"]))
        data = server_info
    else:
        server_info = get_task_info(get_tasks())
        logger.info("Returning general query")
        data = server_info
    
    if data != None:
        return json.dumps({
            "message" : "Success",
            "success" : True,
            "data" : data
        })
    else:
        return json.dumps({
            "message" : "Empty",
            "success" : False,
            "data" : []
        })

def get_task_info(task_id_list):
    if len(task_id_list) == 0:
        return []
    
    response = ecs.describe_tasks(
        cluster=os.environ.get('CLUSTER'),
        tasks=task_id_list
    )

    tasks_info = [] # List containing task info

    # Check each task for server data
    if 'tasks' in response:
        for task in response['tasks']:

            # Check containers for information
            for container in task['containers']:

                # Only check game server containers
                if container['name'] == os.environ.get('CONTAINER_NAME', 'game_server'):

                    # Create object to repersent task info
                    server = {"lobby" : container['taskArn']}

                    # Search network bindings for connection info
                    for binding in container['networkBindings']:
                        # Add binding at server port
                        if binding['containerPort'] == os.environ.get('SERVER_PORT', 7777):
                            server['port'] = binding['hostPort']
                            server['ip'] = get_container_instance_ip(task['containerInstanceArn'])
                            break

                    

                    # Add task to list once it's found port info
                    if 'port' in server and 'ip' in server:
                        tasks_info.append(server)
                        break

    return tasks_info

def get_tasks(page=0):

    current_page = 0 # Current page being listed
    next_token = None # Token used to go to next page
    tasks = [] # List of task arns

    while page <= current_page:
        # List running tasks in cluster
        if next_token:
            response = ecs.list_tasks(
                cluster=os.environ.get('CLUSTER'),
                nextToken=next_token,
                desiredStatus="RUNNING",
                maxResults=10
            )
        else:
            response = ecs.list_tasks(
                cluster=os.environ.get('CLUSTER'),
                desiredStatus="RUNNING"
            )

        if page == current_page:
            # On a valid response return valid tasks
            if 'taskArns' in response:
                tasks = response['taskArns']
        else:
            # Check next page
            if 'nextToken' in response:
                next_token = response['nextToken']
            else:
                break
        current_page = current_page + 1

    return tasks

def get_container_instance_ip(container_instance):
    response = ecs.describe_container_instances(
        cluster=os.environ.get('CLUSTER'),
        containerInstances=[container_instance]
    )
    if 'containerInstances' in response and len(response['containerInstances']) > 0:
        instance = ec2.Instance(response['containerInstances'][0]['ec2InstanceId'])
        return instance.public_ip_address
    
    raise "Container instance not found!"

# CLI for testing lambda
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Lists game servers running on ECS")
    parser.add_argument('-p','--page', default=None, help="Page to return", dest="page")
    parser.add_argument('-l','--lobby', default=None, help="Lobby name to search query for", dest="lobby")

    args = parser.parse_args()

    event = {'queryStringParameters':{}}
    if args.lobby:
        event['queryStringParameters']['server'] = args.lobby
    if args.page:
        event['queryStringParameters']['page'] = args.page

    print(lambda_handler(event,{}))