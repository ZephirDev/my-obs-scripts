import obspython as obs
import sys
import os
import webbrowser
import threading
import requests
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib import parse
import json
import time

parent_directory = os.path.dirname(__file__)
if parent_directory not in sys.path:
      print('Add %s directory to python path to load rel python file.' % parent_directory)
      sys.path.append(parent_directory)

client_id=''
if os.path.exists('%s/twitch.json' % parent_directory):
    with open('%s/twitch.json' % parent_directory, 'r') as f:
        data = json.loads(f.read())
        client_id = data['client_id']

from send_tweet import send_tweet

def script_load(settings):
    def on_stream_starting(event):
        if event == obs.OBS_FRONTEND_EVENT_STREAMING_STARTING:
            message_template_data = {
                'twitch_channel': twitch_channel,
            }

            def get_twitch_channel_data():
                response = requests.get('https://api.twitch.tv/helix/users?login='+twitch_channel,
                                        headers={
                                            'Authorization': 'Bearer %s' % twitch_access_token,
                                            'Client-Id': client_id 
                                        })
                if response.status_code != 200:
                    return {}

                user_id = None
                try:
                    users = json.loads(response.content)
                    if 'data' not in users or len(users['data']) == 0:
                        return {}
                    user_id = users['data'][0]['id']
                except:
                    return {}

                response = requests.get('https://api.twitch.tv/helix/channels?broadcaster_id=' + str(user_id),
                                        headers={
                                            'Authorization': 'Bearer %s' % twitch_access_token,
                                            'Client-Id': client_id 
                                        })
                if response.status_code != 200:
                    return {}
                
                try:
                    channels = json.loads(response.content)
                    if 'data' not in channels or len(channels['data']) == 0:
                        return {}
                    return channels['data'][0]
                except:
                    return {}

            if require_twitch_channel_data_for_template and twitch_access_token != '':
                message_template_data.update(get_twitch_channel_data())
            
            send_tweet(message_template % message_template_data)
             

    obs.obs_frontend_add_event_callback(on_stream_starting)

def script_description():
	return "Send a tweet when you start streaming with obs.\n\nBy ZephyrDevelop"

def script_update(settings):
    global require_twitch_channel_data_for_template
    global message_template
    global twitch_channel
    global twitch_access_token

    require_twitch_channel_data_for_template = obs.obs_data_get_bool(settings, "require_twitch_channel_data_for_template")
    twitch_channel      = obs.obs_data_get_string(settings, "twitch_channel")
    message_template    = obs.obs_data_get_string(settings, "message_template")
    twitch_access_token = ''
    if os.path.exists('%s/twitch_access_token' % parent_directory):
        with open('%s/twitch_access_token' % parent_directory, 'r') as f:
            twitch_access_token = f.read()


def script_defaults(settings):
    obs.obs_data_set_default_bool(settings, "require_twitch_channel_data_for_template", True)
    obs.obs_data_set_default_string(settings, "twitch_channel", "zephyrdevelop")
    obs.obs_data_set_default_string(settings, "twitch_access_token", "")
    obs.obs_data_set_default_string(settings, "message_template", "Rejoins moi sur twitch pour '%(title)s' sur '%(game_name)s'. https://www.twitch.tv/%(twitch_channel)s")

def handle_twitch_access_token(props, prop):
    global server
    class handler(BaseHTTPRequestHandler):
        def do_GET(self):
            global twitch_access_token

            if self.path == '/':
                self.send_response(200)
                self.send_header('Content-type','text/html')
                self.end_headers()
                self.wfile.write("""
                <html>
                    <body>
                        <script>
                            window.location.href = 'http://localhost:15000?'+document.location.href.split('#').pop();
                        </script>
                    </body>
                </html>
                """.encode())
                return
    
            self.send_response(200)
            self.send_header('Content-type','text/html')
            self.end_headers()

            url = parse.urlparse(self.path)
            query = parse.parse_qs(url.query)
            twitch_access_token = query['access_token']
            if isinstance(twitch_access_token, list):
                twitch_access_token = twitch_access_token[0]
            self.wfile.write('You can close this window. OBS has fetch the access_token.'.encode())
            self.wfile.flush()

            def stop_later():
                time.sleep(1)
                server.shutdown()
                server.server_close()

            threading.Thread(target=stop_later).start()

            with open('%s/twitch_access_token' % parent_directory, 'w') as f:
                f.write(twitch_access_token)

    server = HTTPServer(('localhost', 15000), handler)
    def start():
        print('Oauth server is running')
        server.serve_forever()
        print('Oauth server is killed')
    threading.Thread(target=start).start()
    webbrowser.open('https://id.twitch.tv/oauth2/authorize?response_type=token&client_id=%s&redirect_uri=http://localhost:15000&scope=' % client_id)


def script_properties():
    props = obs.obs_properties_create()

    obs.obs_properties_add_bool(props, "require_twitch_channel_data_for_template", "Fetch data from twitch channel before generate the tweet message.")
    obs.obs_properties_add_text(props, "twitch_channel", "My twitch channel", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_text(props, "message_template", "My tweet message template", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_button(props, "oauth_token", "Grant access to twitch api", handle_twitch_access_token)

    return props
