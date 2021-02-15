import json
from elasticsearch import Elasticsearch, RequestsHttpConnection, helpers
from requests_aws4auth import AWS4Auth
import boto3
import random
import re
freq = 300
BATCH_LIM = 52
host = 'search-cc-hw1-44vuhvpon2yqqgfpqp42jmvv2m.us-east-1.es.amazonaws.com'
region = 'us-east-1' # e.g. us-west-1
TABLE_NAME = 'yelp-restaurants'
service = 'es'
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)
es = Elasticsearch(
    hosts = [{'host': host, 'port': 443}],
    http_auth = awsauth,
    use_ssl = True,
    verify_certs = True,
    connection_class = RequestsHttpConnection
)
sqs = boto3.client('sqs')
sqs_url = 'https://queue.amazonaws.com/387645926509/messageQueue.fifo'
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table(TABLE_NAME)
table_users = dynamodb.Table('users')
sns = boto3.client('sns')
def get_sqs():
    response = {'Messages': None}
    messages = []
    while 'Messages' in response.keys():
        response = sqs.receive_message(
            QueueUrl=sqs_url,
            AttributeNames=[
                'All'
            ],
            MaxNumberOfMessages=10,
            MessageAttributeNames=[
                'All'
            ],
            VisibilityTimeout=30,
            WaitTimeSeconds=0
        )
        if 'Messages' in response.keys():
            messages.extend(response['Messages'])
    to_return = []
    for message in messages:
        to_return.append({
            'user_id': message['Attributes']['MessageGroupId'],
            'request': json.loads(message['Body'])
        })
    sqs.purge_queue(QueueUrl=sqs_url)
    return to_return
def generate_query(categories):
    query_body = {
        "query": {
            "match": {
                "categories": categories
            }
        }}
    return [{'index': TABLE_NAME}, query_body]
def generate_queries(users):
    cates = []
    for user in users:
        cates.append(user['request']['Cuisine'])
    queries = []
    for cate in cates:
        queries.extend(generate_query(cate))
    return queries
def get_res_id(queries):
    responses = []
    for i in range(0, len(queries), freq):
        responses.extend(es.msearch(body=queries[int(i): int(i+freq)])['responses'])
    recom = []
    for rep in responses:
        if len(rep['hits']['hits']) == 0:
            recom.append('random')
        else:
            selection = random.choice(range(len(rep['hits']['hits'])))
            recom.append(rep['hits']['hits'][selection]['_id'])
    return recom
def generate_recom():
    user_quotas = get_sqs()
    queries = generate_queries(user_quotas)
    recoms = get_res_id(queries)
    for quota, recom in zip(user_quotas, recoms):
        quota['restaurant_id'] = recom
    return user_quotas
def generate_message_quotas():
    user_recom = generate_recom()
    rest_info = []
    for i in range(0, len(user_recom), BATCH_LIM):
        rest_info.extend(dynamodb.batch_get_item(
            RequestItems={
                table.name:{
                        'Keys': [{'id': recom['restaurant_id']}for recom in user_recom[i: i+BATCH_LIM]],
                    'AttributesToGet': ['id', 'address', 'name']
                    }
            }
        )['Responses'][table.name])
    num_random = len(user_recom) - len(rest_info)
    if num_random > 0:
        random_set = table.scan(AttributesToGet =  ['id', 'address', 'name'], Limit = num_random)['Items']
        cur_idx = 0
        while len(random_set) < num_random:
            random_set.extend(random_set[cur_idx])
            cur_idx += 1
    rest_indx = {}
    for res in rest_info:
        rest_indx[res['id']] = {'name': res['name'], 'address': res['address']}
    for recom in user_recom:
        if recom['restaurant_id'] == 'random':
            random_idx = random.choice(range(len(random_set)))
            recom['restarurant_name'] = random_set[random_idx]['name']
            recom['restarurant_address'] = ','.join(random_set[random_idx]['address'])
        else:
            recom['restarurant_name'] = rest_indx[recom['restaurant_id']]['name']
            recom['restarurant_address'] = ','.join(rest_indx[recom['restaurant_id']]['address'])
    return user_recom
def generate_message(quota):
    toReturn = f'''Hello! 
Here is my {quota['request']['Cuisine']} restaurant suggestion for {quota['request']['NumberOfPeople']},
Time: {quota['request']['DiningDate']} at {quota['request']['DiningTime']},
Restaurant: {quota['restarurant_name']},
Address: {quota['restarurant_address']}.
Enjoy your meal!'''
    return toReturn
def generate_messages(message_quotas):
    output = [{'user_id': quota['user_id'],
                'PhoneNumber': quota['request']['PhoneNumber'], 
                'Message': generate_message(quota)} for \
            quota in message_quotas]
    return output

def lambda_handler(event, context):
    message_quotas = generate_message_quotas()
    if len(message_quotas) == 0:
        return
    records = [{'user_id': quotas['user_id'], 
    'request': {'Location': quotas['request']['Location'],
                'Cuisine': quotas['request']['Cuisine']}}for quotas in  message_quotas]
    messages = generate_messages(message_quotas)
    print(messages)
    for message in messages:
        sns.set_sms_attributes(attributes={'DefaultSMSType': 'Transactional'})
        sns.publish(
            PhoneNumber = "+1"+re.findall(r'(\d+)', message['PhoneNumber'])[0][-10:],
            Message = message['Message']
        )
    with table_users.batch_writer(overwrite_by_pkeys=['id']) as batch:
        for record in records:
            batch.delete_item(
                Key={
                    'id': record['user_id']
                }
            )
            batch.put_item(
                Item={
                    'id': record['user_id'],
                    'Cuisine': record['request']['Cuisine'],
                    'Location': record['request']['Location']
                }
            )