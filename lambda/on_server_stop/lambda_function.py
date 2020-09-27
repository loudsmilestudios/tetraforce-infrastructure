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
    
    for task_arn in event["resources"]:

        # Lookup item in table
        aws_resp = table.get_item(
            Key={"task" : task_arn}
        )

        # Verify item exists
        if not 'Item' in aws_resp:
            logger.error(f"The server you are trying to stop does not exist: {task_arn}")
        if not 'task' in aws_resp['Item']:
            logger.error(f"The server you are trying to stop does not have an associated task: {task_arn}")

        if 'task' in aws_resp:
            # Delete item from dynamo table
            table.delete_item(
                Key={ "task" : task_arn }
            )
        else:
            logger.error(aws_resp)