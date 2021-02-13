import json
import time
import boto3
from decimal import Decimal
TABLE_NAME = 'yelp-restaurants'
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
restarurants = json.load(open('./restarurants.json'), parse_float=Decimal)

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
    time.sleep(5)
    return table

if __name__ == '__main__':
    table = create_yelp_table()
    with table.batch_writer() as batch:
        for restarurant in restarurants:
            batch.put_item(
                        Item={
                        'id': restarurant['id'],
                        'insertedAtTimestamp': int(time.time()),
                        'name': restarurant['name'],
                        'alias': restarurant['alias'],
                        'address': restarurant['address'],
                        'latitude': restarurant['latitude'],
                        'review_count': restarurant['review_count'],
                        'rating': restarurant['rating'],
                        'zip_code': restarurant['zip_code'],
                        'categories': restarurant['categories']
                    })
    dynamodb.create_table(
        TableName='users',
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