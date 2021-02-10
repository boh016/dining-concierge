import requests
import time
import json
import boto3
from tqdm import tqdm
from decimal import Decimal
API_KEY  = json.load(open('./yelp_api_key.json'))
TABLE_NAME = 'yelp-restaurants'
YELP_API = 'https://api.yelp.com/v3/businesses/search'
DEFAULT_LOCATION = 'Manhattan, New York'
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
TOTAL = 5000
params = {
    'location': DEFAULT_LOCATION,
    'limit': 50,
    'term':"restaurants",
    'sort_by': 'review_count'
}
def fetch_info(credential, params, offset):
    pram = params.copy()
    pram['offset'] = offset
    resp = requests.get(YELP_API, headers=credential, params=params)
    assert resp.status_code == 200
    records = resp.json()['businesses']
    return records
def create_yelp_table(dynamodb=None):
    if not dynamodb:
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    try:
        if dynamodb.Table(TABLE_NAME).table_status == 'ACTIVE':
            return dynamodb.Table(TABLE_NAME)
    except:
        pass
    table = dynamodb.create_table(
        TableName=TABLE_NAME,
        KeySchema=[
            {
                'AttributeName': 'id',
                'KeyType': 'HASH'  # Partition key
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'id',
                'AttributeType': 'S'
            }
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 10,
            'WriteCapacityUnits': 10
        }
    )
    return table
def parse_data(data):
    processed_data = {
        'id': data['id'],
        'name': data['name'],
        'alias': data['alias'],
        'rating': data['rating'],
        'address': data['location']['display_address'],
        'latitude': float(data['coordinates']['latitude']),
        'longitude': float(data['coordinates']['longitude']),
        'review_count': int(data['review_count']),
        'zip_code': data['location']['zip_code'],
        'categories': [i['title'] for i in data['categories']],
        'price': int(len(data['price']))
    }
    return json.loads(json.dumps(processed_data), parse_float=Decimal)
def put_restarurant(table, data, dynamodb=None):
    if not dynamodb:
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    assert table.table_status == 'ACTIVE'
    processed_data = parse_data(data)
    response = table.put_item(
        Item={
            'id': processed_data['id'],
            'insertedAtTimestamp': int(time.time()),
            'name': processed_data['name'],
            'alias': processed_data['alias'],
            'address': processed_data['address'],
            'latitude': processed_data['latitude'],
            'review_count': processed_data['review_count'],
            'rating': processed_data['rating'],
            'zip_code': processed_data['zip_code'],
            'categories': processed_data['categories'],
            'price': processed_data['price']
        }
    )
    return response

if __name__ == '__main__':
    auth = API_KEY
    table = create_yelp_table(dynamodb)
    num_recorded = 0
    offset = 0
    pbar = tqdm(total=TOTAL)
    while num_recorded < TOTAL:
        records = fetch_info(auth, params, offset)
        for data in records:
            if 'alias' in data.keys():
                resp = put_restarurant(table, data, dynamodb)
                if resp['ResponseMetadata']['HTTPStatusCode'] == 200:
                    num_recorded += 1
                    pbar.update(1)
        offset += 1