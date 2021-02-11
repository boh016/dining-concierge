import json
from elasticsearch import Elasticsearch, RequestsHttpConnection, helpers
from requests_aws4auth import AWS4Auth
import boto3
from tqdm import tqdm
import time
freq = 300
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
restaurants = json.load(open('./restaurants.json'))
actions = []
for res in restaurants:
    actions.append({
    "_index": TABLE_NAME,
    "_type": "restaurants",
    "_id": res['id'],
    "_source": {
        "address": res['address'],
        "categories": res['categories']
    }})


if __name__ == '__main__':
    for i in tqdm(range(0, len(actions), freq)):
        helpers.bulk(es, actions[i: i+freq])
        time.sleep(5)