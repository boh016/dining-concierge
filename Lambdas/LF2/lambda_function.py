import json
from elasticsearch import Elasticsearch, RequestsHttpConnection, helpers
from requests_aws4auth import AWS4Auth
import boto3
import random
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
        cates.append(user['categories'])
    queries = []
    for cate in cates:
        queries.extend(generate_query(cate))
    return queries

def get_res_id(queries):
    responses = []
    for i in range(0, len(queries), freq):
        responses.extend(es.msearch(body=queries[i, i+freq]))
    recom = []
    for rep in responses['responses']:
        if len(rep['hits']['hits']) == 0:
            recom.append('random')
        else:
            selection = random.choice(range(len(rep['hits']['hits'])))
            recom.append(rep['hits']['hits'][selection]['_id'])
    return recom



def lambda_handler(event, context):
    return