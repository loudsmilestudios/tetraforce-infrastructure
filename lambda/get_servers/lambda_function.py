import os, logging, boto3, json

if __name__ != "__main__":
    from aws_xray_sdk.core import xray_recorder
    from aws_xray_sdk.core import patch_all
    patch_all()

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ec2 = boto3.client('ec2')
ecs = boto3.client('ecs')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ.get("SERVERLIST_TABLE"))

def lambda_handler(event, context):
    data = None

    # Looks up information for specific server
    if "queryStringParameters" in event and "server" in event["queryStringParameters"]:
        logger.info("Returning queried server: " + event["queryStringParameters"]["server"])
        result = table.get_item(
            Key={"name" : event["queryStringParameters"]["server"] }
        )
        if 'Item' in result:
            data = replace_dynamo_with_data(result['Item'])

    # Lookup information for specified page
    elif "queryStringParameters" in event and "page" in event["queryStringParameters"]:
        logger.info("Returning page: " + str(event["queryStringParameters"]["page"]))
        data = get_server_list(int(event["queryStringParameters"]["page"]))
    else:
        # Lookup page 0
        logger.info("Returning general query")
        data = get_server_list()
    
    # Return data
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

page_size = 20
max_page_count = os.environ.get("MAX_PAGE_COUNT", 10)
def get_server_list(page=0):
    if page > max_page_count:
        page = max_page_count
    resp = table.scan(Limit=page_size,Select='ALL_ATTRIBUTES')

    # Loop through number of pages after intial page (0)
    for _ in range(page):
        if 'Items' in resp:
            if 'LastEvaluatedKey' in resp:
                resp = table.scan(Limit=page_size,Select='ALL_ATTRIBUTES',ExclusiveStartKey=resp['LastEvaluatedKey'])
        else:
            resp = {}
    
    if 'Items' in resp:
        items = resp['Items']
        
        # Use function to replace `task` with ip and port information
        for item in items:
            item = replace_dynamo_with_data(item)
        return items

    else:
        return []

# Replaces task with ip and port
def replace_dynamo_with_data(dynamo_item):
    task = dynamo_item['task']
    del dynamo_item['task']

    info = get_task_info([task])
    dynamo_item['ip'] = info[0]['ip']
    dynamo_item['port'] = info[0]['port']

    return dynamo_item

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
                    server = {"lobby" : container['taskArn'], "port" : os.environ.get('SERVER_PORT', 7777)}

                    # Search network bindings for connection info
                    interfaces = ec2.describe_network_interfaces(
                            Filters=[
                                {
                                    "Name": "addresses.private-ip-address",
                                    "Values": [
                                        container["networkInterfaces"][0]["privateIpv4Address"],
                                    ]
                                },
                            ]
                        )
                    
                    # If container has attached network interface
                    if len(interfaces["NetworkInterfaces"]) > 0:
                        server["ip"] = interfaces["NetworkInterfaces"][0]["Association"]["PublicIp"]
                        tasks_info.append(server)
            
            # Check task status
            task_info["status"] = task["lastStatus"]

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