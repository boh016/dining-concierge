import json
import boto3

client = boto3.resource('sqs')
def lambda_handler(event, context):
    msg = event['currentIntent']['slots'].copy()
    queue = client.get_queue_by_name(QueueName = 'messageQueue.fifo')
    rsp = queue.send_message(MessageBody=json.dumps(msg), MessageGroupId=event['userId'])
    return {
        # "sessionAttributes": event['sessionAttributes'],
        # "recentIntentSummaryView", event['recentIntentSummaryView'],
        "dialogAction": {
          "intentName": "DiningSuggestions",
          "type": "ConfirmIntent",
          "message": {
            "contentType": "PlainText",
            "content": "You're all set. Expect my suggestion shortly! Have a good day."
          }
        }}