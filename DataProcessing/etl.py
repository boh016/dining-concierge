import requests
import time
import json
import pandas as pd
API_KEY  = json.load(open('../.././yelp_api_key.json'))
YELP_API = 'https://api.yelp.com/v3/businesses/search'
LOCATIONS = [10026, 10027, 10030, 10037, 10039,10001, 10011, 10018, 10019, 
            10020, 10036,10029, 10035,10010, 10016, 10017, 10022,
            10012, 10013, 10014,
            10004, 10005, 10006, 10007, 10038, 10280,
            10002, 10003, 10009,10021, 10028, 10044, 10065, 10075, 
            10128,10023, 10024, 10025,10031, 10032, 10033, 10034, 10040]
TOTAL = 5000
def fetch_info(credential, params):
    resp = requests.get(YELP_API, headers=credential, params=params)
    counter = 0
    while resp.status_code != 200:
        time.sleep(5)
        resp = requests.get(YELP_API, headers=credential, params=params)
        if counter == 3:
            assert resp.status_code == 200
    records = resp.json()['businesses']
    return records
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
    }
    return processed_data

if __name__ == '__main__':
    auth = API_KEY
    params = {
    'location': None,
    'limit': 50,
    'term':"restaurants",
    'sort_by': 'review_count',
    'offset': None
    }
    output = []
    for location in LOCATIONS:
        params['location'] = location
        for offset in range(0, 600, 50):
            params['offset'] = offset
            print(params)
            records = fetch_info(auth, params)
            for data in records:
                if 'alias' in data.keys():
                    output.append(data)
            time.sleep(1)
    df = pd.DataFrame(output).drop_duplicates(subset='id')\
        .sort_values(['rating', 'review_count'], ascending=False).iloc[:TOTAL, :]
    output = []
    for i in range(df.shape[0]):
        output.append(parse_data(df.iloc[i, :].to_dict()))
    with open('./restaurants.json', 'w+') as f:
        json.dump(output, f)