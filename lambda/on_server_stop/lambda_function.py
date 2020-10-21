import os, logging, boto3, json

if __name__ != "__main__":
    from aws_xray_sdk.core import xray_recorder
    from aws_xray_sdk.core import patch_all
    patch_all()

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ.get("SERVERLIST_TABLE"))

def lambda_handler(event, context):
    
    task = event["detail"]

    # Lookup item in table
    aws_resp = table.query(
        IndexName="task",
        KeyConditionExpression="task = :a",
        ExpressionAttributeValues= {
            ":a": task["taskArn"]
        }
    )

    # Verify item exists
    if not 'Items' in aws_resp or len(aws_resp['Items']) == 0:
        logger.error(f"The server you are trying to stop does not exist: {task['taskArn']}")
    if not 'task' in aws_resp['Items'][0]:
        logger.error(f"The server you are trying to stop does not have an associated task: {task['taskArn']}")
    if task["desiredStatus"] != "STOPPED":
        logger.warning(f"Task '{task['taskArn']}' not stopped ignoring!")
    elif 'task' in aws_resp['Items'][0]:
        # Delete item from dynamo table
        logger.info(f"Removing {aws_resp['Items'][0]['name']} from database")
        table.delete_item(
            Key={ "name" : aws_resp['Items'][0]["name"] }
        )
    else:
        logger.error(aws_resp)