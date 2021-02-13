import math
import dateutil.parser
import datetime
import time
import os
import json
import boto3
import logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
sqs = boto3.resource('sqs')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('users')
""" --- Helper Functions --- """
def parse_int(n):
    try:
        return int(n)
    except ValueError:
        return float('nan')
def build_validation_result(is_valid, violated_slot, message_content):
    if message_content is None:
        return {
            "isValid": is_valid,
            "violatedSlot": violated_slot,
        }

    return {
        'isValid': is_valid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': message_content}
    }
def isvalid_date(date):
    try:
        dateutil.parser.parse(date)
        return True
    except ValueError:
        return False
def delegate(session_attributes, slots):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }
def get_slot(intent_request):
    return get_slot(intent_request)['slots']
""" --- Hard Code Intent Functions --- """
def greeting_intent(intent_request):
    return {
        'dialogAction': {
            "type": "ElicitIntent",
            'message': {
                'contentType': 'PlainText',
                'content': 'Hi there, how can I help?'}
        }
    }
def thank_you_intent(intent_request):
    return {
        'dialogAction': {
            "type": "Close",
            'message': {
                'fulfillmentState': 'fulfilled',
                'contentType': 'PlainText',
                'content': 'You are welcome!'}
        }
    }
def confirmation_intent(location, cuisine):
    return {
            'dialogAction': {
            'type': 'ConfirmIntent',
            'intentName': 'DiningSuggestionsIntent',
            'slots': {
                    'Location': location,
                    'Cuisine': cuisine
                    },
            'message': {
                'contentType': 'PlainText',
                'content':f'I detect you have a dining suggestion in my history, Do you want to reuse the Location: {location} and Cuisine {cuisine} from last time?'
                }
                }
            }

    

""" --- Logic Intent Functions --- """
def dining_suggestion_intent(intent_request):
    location = get_slot(intent_request)["Location"]
    cuisine = get_slot(intent_request)["Cuisine"]
    num_people = get_slot(intent_request)["NumberOfPeople"]
    date = get_slot(intent_request)["Date"]
    time = get_slot(intent_request)["Time"]
    source = intent_request['invocationSource']
    if all([i is None for i in [location, cuisine, num_people, date, time]]):
        table_resp = table.get_item(
            Key = {'id':intent_request['userId']}
        )
        if 'Item' in table_resp.keys():
            if 'confirmationStatus' in intent_request['currentIntent'].keys():
                if intent_request['currentIntent']['confirmationStatus'] == 'Confirmed':
                    location = intent_request['currentIntent']['slots']['Location']
                    cuisine = intent_request['currentIntent']['slots']['Cuisine']
                elif intent_request['currentIntent']['confirmationStatus'] == 'Denied':
                    pass
                else:
                    return confirmation_intent(location, cuisine)
            else:
                prev_location = table_resp['Item']['Location']
                prev_cuisine = table_resp['Item']['Cuisine']
                return confirmation_intent(location, cuisine)
        else:
            pass
    if source == 'DialogCodeHook':
        if intent_request[
            'sessionAttributes'] is not None:
            output_session_attributes = intent_request['sessionAttributes']
        else:
            output_session_attributes = {}
        return delegate(output_session_attributes, {
            'Location': location,
            'Cuisine': cuisine,
            'NumberOfPeople': num_people,
            'Date': date,
            'Time': time,
            })
    msg = intent_request['currentIntent']['slots'].copy()
    queue = sqs.get_queue_by_name(QueueName = 'messageQueue.fifo')
    rsp = queue.send_message(MessageBody=json.dumps(msg), MessageGroupId=intent_request['userId'])
    return {
        "dialogAction": {
        "intentName": "DiningSuggestions",
        "type": "Close",
        "fulfillmentState": "Fulfilled",
        "message": {
        "contentType": "PlainText",
        "content": "You're all set. Expect my suggestion shortly! Have a good day."
        }}}


""" --- Main handler --- """
def dispatch(intent_request):
    logger.debug('dispatch userId={}, intentName={}'.format(intent_request['userId'], get_slot(intent_request)['name']))
    intent_name = get_slot(intent_request)['name']
    if intent_name == 'GreetingIntent':
        return greeting_intent(intent_request)
    if intent_name == 'DiningSuggestionsIntent':
        return dining_suggestion_intent(intent_request)
    if intent_name == 'ThankYouIntent':
        return thank_you_intent(intent_request)


def lambda_handler(event, context):
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    logger.debug('event.bot.name={}'.format(event['bot']['name']))
    return dispatch(event)