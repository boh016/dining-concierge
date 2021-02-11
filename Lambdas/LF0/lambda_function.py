import json
import boto3

client = boto3.client('lex-runtime')

def lambda_handler(event, context):
    message = event['message'];
    user = event['user_id']
    messages = {'messages': []}
    response = client.post_text(botName='ScheduleAppointment',
                                botAlias='dev',
                                userId=user,
                                inputText=message)
    if 'message' in response.keys():
        messages['messages'].append({'type':'unstructured', 
                                    'unstructured': {'text':response['message']}})
        
    return  {
    'statusCode': 200,
    'data': json.dumps(messages)
    }

