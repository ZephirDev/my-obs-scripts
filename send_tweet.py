import requests
import json
import random
import urllib
import time
import base64
import hmac
import hashlib
import os
import json

twitter_api_scheme='https'
twitter_api_host='api.twitter.com'
twitter_api='%s://%s' % (twitter_api_scheme, twitter_api_host)
consumer_key=''
consumer_secret=''
access_token=''
access_token_secret=''

parent_directory = os.path.dirname(__file__)
if os.path.exists('%s/twitter.json' % parent_directory):
    with open('%s/twitter.json' % parent_directory, 'r') as f:
        data = json.loads(f.read())
        consumer_key = data['consumer_key']
        consumer_secret = data['consumer_secret']
        access_token = data['access_token']
        access_token_secret = data['access_token_secret']
    


def encodeURIComponent(str):
    return urllib.parse.quote(str, safe='~()*!\'')

def generate_authorization_header(method, path, data):
    nonce = ''.join((random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789') for i in range(11)))
    parameters = [
        ('oauth_consumer_key', consumer_key),
        ('oauth_token', access_token),
        ('oauth_nonce', nonce),
        ('oauth_signature_method', 'HMAC-SHA1'),
        ('oauth_version', '1.0'),
        ('oauth_timestamp', int(time.time()))
    ]
    parameters.sort(key=lambda i: i[0])
    
    parameter_string = ''
    clone = []
    clone.extend(parameters)
    clone.extend(data.items())
    clone.sort(key=lambda i: i[0])

    for field, value in clone:
        if parameter_string != '':
            parameter_string += '&'
        parameter_string += '%s=%s' % (field, value)

    oauth_base_string = '%s&%s&%s' % (method, encodeURIComponent(twitter_api+path), encodeURIComponent(parameter_string))
    oauth_signing_key = '%s&%s' % (encodeURIComponent(consumer_secret), encodeURIComponent(access_token_secret))
    
    s = hmac.new(oauth_signing_key.encode(), oauth_base_string.encode(), hashlib.sha1).digest()
    signature = base64.b64encode(s).decode()
    
    parameters.append(('oauth_signature', encodeURIComponent(signature)))
    token = ''
    for field, value in parameters:
        if token != '':
            token += ','
        token += '%s=\"%s\"' % (field, value)

    return 'OAuth %s' % token

def send_tweet(text):
    bearer = generate_authorization_header('POST', '/2/tweets', {})
    response = requests.post('%s/2/tweets' % twitter_api,
                  headers={
                      'Authorization': bearer,
                  },
                  json={
                    'text': text
                  })
    
    if response.status_code not in [200, 201]:
        raise Exception('%d %s' % (response.status_code, response.content))
