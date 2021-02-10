import json
import boto3

client = boto3.client('lex-runtime')

def lambda_handler(event, context):
    print(event)
    last_user_message = event['messages'];

    response = client.post_text(botName='DiningSuggestions',
                                botAlias='dev',
                                userId=user,
                                inputText=last_user_message)

    if response['message'] is not None or len(response['message']) > 0:
        last_user_message = response['message']

    return {
        'statusCode': 200,
        'body': json.dumps(last_user_message)
    }
