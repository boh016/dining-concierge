# dining-concierge

## Contribution
Hu, Bo (UNI: bh2569)

Yuan, Jackie (UNI: sy2938)

## Description of Content

```bash
├── ApiGateway #api config file
│   └── api.yaml
├── DataProcessing #scripts for data processing
│   ├── dynamodb.py
│   ├── es.py
│   ├── etl.py
│   ├── requirements.txt
│   └── restaurants.json #scrapped 5000 NYC restaurants from YELP API
├── LICENSE
├── Lambdas
│   ├── DecodeToken #cognito token decoding function
│   ├── LF0
│   ├── LF1
│   ├── LF2
│   └── lexConfig.json #lex config file
├── README.md
└── Webpage
```

## AWS Services

- Amazon Cognito
  - for user identification from Google API
- Amazon S3
  - for hosting front-end website
- Amazon CloudFront
  - for distributing https distribution of the website
- Amazon API Gateway
  - for managing APIs
- Amazon Lex
  - for NLP-based chatting bot
- Amazon SQS
  - for queueing up users' requests
- Amazon DynamoDB
  - for storing restaurants' information from Yelp API
  - for storing users' previous search history
- Amazon ElasticSearch
  - for searching restaurants' index based on users' preferences
- Amazon Lambda
  - LF0
    - for establish communication between website and Amazon Lex
  - LF1
    - for establish communication between Amazon Lex and Amazon SQS
  - LF2
    - for pulling data from DynamoDB and ElasticSearch and sending message from Amazon SQS to Amazon SNS
