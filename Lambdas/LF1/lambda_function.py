import math
import dateutil.parser
import datetime
import time
import os
import json
import boto3
import logging
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
    return intent_request['currentIntent']['slots']
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
            'fulfillmentState': 'Fulfilled',
            'message': {
                'contentType': 'PlainText',
                'content': 'You are welcome!'}
        }
    }



""" --- Logic Intent Functions --- """
def load_history_intent(intent_request):
    source = intent_request['invocationSource']
    if source == 'DialogCodeHook' and intent_request['currentIntent']['confirmationStatus'] == 'None':
        resp = table.get_item(Key={'id': intent_request['userId']})
        if 'Item' in resp.keys():
            location,cuisine  = resp['Item']['Location'], resp['Item']['Cuisine']
            return {
                'sessionAttributes': intent_request['sessionAttributes'],
                'dialogAction': {
                        'type': 'ConfirmIntent',
                        'intentName': 'LoadHistory',
                        'message': {'contentType': 'PlainText',
                                    'content': f'Do you want to user cuisine: {cuisine}, location: {location} from last time?'}
                        }
                    }
        else:
            return {
                    'sessionAttributes': intent_request['sessionAttributes'],
                    'dialogAction': {
                        'type': 'ElicitSlot',
                        'intentName': 'DiningSuggestions',
                        'slotToElicit': 'Cuisine',
                        'message': {'contentType': 'PlainText',
                                    'content': 'What cuisine/food would you like to try?'}
                        }
                    }
    if intent_request['currentIntent']['confirmationStatus'] == 'Confirmed':
        resp = table.get_item(Key={'id': intent_request['userId']})
        location,cuisine  = resp['Item']['Location'], resp['Item']['Cuisine']
        return {
                'sessionAttributes': intent_request['sessionAttributes'],
                'dialogAction': {
                    'type': 'ElicitSlot',
                    'intentName': 'DiningSuggestions',
                    'slots': {
                                    'Location': location,
                                    'Cuisine': cuisine,
                                },
                    'slotToElicit': 'DiningDate',
                    'message': {'contentType': 'PlainText',
                                'content': 'What date?'}
                    }
                }
    elif intent_request['currentIntent']['confirmationStatus'] == 'Denied':
        location, cuisine = None, None
        return {
                'sessionAttributes': intent_request['sessionAttributes'],
                'dialogAction': {
                    'type': 'ElicitSlot',
                    'intentName': 'DiningSuggestions',
                    'slotToElicit': 'Cuisine',
                    'message': {'contentType': 'PlainText',
                                'content': 'What cuisine/food would you like to try?'}
                    }
                }




def dining_suggestion_intent(intent_request):
    location = get_slot(intent_request)["Location"]
    cuisine = get_slot(intent_request)["Cuisine"]
    num_people = get_slot(intent_request)["NumberOfPeople"]
    date = get_slot(intent_request)["DiningDate"]
    time = get_slot(intent_request)["DiningTime"]
    phone = get_slot(intent_request)["PhoneNumber"]
    source = intent_request['invocationSource']
    if source == 'DialogCodeHook':
        if intent_request['sessionAttributes'] is not None:
            output_session_attributes = intent_request['sessionAttributes']
        else:
            output_session_attributes = {}
        if num_people is not None:
            num_people = int(num_people)
            if num_people > 20 or num_people < 0:
                return {
                            'sessionAttributes': intent_request['sessionAttributes'],
                            'dialogAction': {
                                'type': 'ElicitSlot',
                                'intentName': intent_request['currentIntent']['name'],
                                'slots': {
                                    'Location': location,
                                    'Cuisine': cuisine,
                                    'NumberOfPeople': None,
                                    'DiningDate': date,
                                    'DiningTime': time,
                                    'PhoneNumber': phone
                                },
                                'slotToElicit': 'NumberOfPeople',
                                'message': {'contentType': 'PlainText',
                                            'content': 'Maximum 20 people allowed. Please Try again'}
                            }
                        }
        return delegate(output_session_attributes, {
            'Location': location,
            'Cuisine': cuisine,
            'NumberOfPeople': num_people,
            'DiningDate': date,
            'DiningTime': time,
            'PhoneNumber': phone
            })
    msg = intent_request['currentIntent']['slots'].copy()
    queue = sqs.get_queue_by_name(QueueName = 'messageQueue.fifo')
    rsp = queue.send_message(MessageBody=json.dumps(msg), MessageGroupId=intent_request['userId'])
    return {
        "dialogAction": {
        "type": "Close",
        "fulfillmentState": "Fulfilled",
        "message": {
        "contentType": "PlainText",
        "content": "You're all set. Expect my suggestion shortly! Have a good day."
        }}}


""" --- Main handler --- """
def dispatch(intent_request):
    intent_name = intent_request['currentIntent']['name']
    if intent_name == 'Greeting':
        return greeting_intent(intent_request)
    if intent_name == 'DiningSuggestions':
        return dining_suggestion_intent(intent_request)
    if intent_name == 'LoadHistory':
        return load_history_intent(intent_request)
    if intent_name == 'ThankYou':
        return thank_you_intent(intent_request)


def lambda_handler(event, context):
    
    print(event)
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    return dispatch(event)