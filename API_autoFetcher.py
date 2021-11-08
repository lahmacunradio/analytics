import requests
import datetime
import threading
import pandas as pd

'''
import custom module 'access.py' to access your own API token and log in:

$ cat access.py 
MY_KEY = "Bearer xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
'''
import access
API_KEY = access.MY_KEY

monitored_data = {
    'ip': [],
    'location': [],
    'connected_time': [],
    'valid': []
}


def snapshot(minutes_threshold):

    headers = {'Authorization': API_KEY}
    res = requests.get('https://streaming.lahmacun.hu/api/station/1/listeners', headers=headers)
    results = res.json()

    minutes_threshold = datetime.timedelta(minutes=minutes_threshold)

    for listener in results:

        connected_time = listener['connected_time']
        connected_time = datetime.timedelta(seconds=connected_time)

        ip = listener['ip']

        if listener['location']['status'] == 'error':
            loc = 'N/A'
        else:
            loc = listener['location']['country']

        # if user is/has been already listening
        if ip in monitored_data['ip']:
            i = monitored_data['ip'].index(ip)
            if connected_time >= monitored_data['connected_time'][i][-1][1]:
                monitored_data['connected_time'][i][-1][1] = connected_time
                if connected_time > minutes_threshold:
                    monitored_data['valid'][i] = 1
                else:
                    monitored_data['valid'][i] = 0
            else:
                monitored_data['connected_time'][i].append([datetime.datetime.now(), connected_time])
                if connected_time > minutes_threshold:
                    monitored_data['valid'][i] = 1
                else:
                    monitored_data['valid'][i] = 0

        # if new user is detected
        else:
            monitored_data['ip'].append(ip)
            monitored_data['location'].append(loc)
            monitored_data['connected_time'].append([[datetime.datetime.now(), connected_time]])

            if connected_time > minutes_threshold:
                monitored_data['valid'].append(1)
            else:
                monitored_data['valid'].append(0)

def autoFetch(minutes_threshold = 5):
    threading.Timer(30.0, autoFetch).start()
    snapshot(minutes_threshold)

def autoExport(n_hours = 24):
    n_seconds = n_hours * 3600.0
    threading.Timer(n_seconds, autoExport).start()
    timestamp = datetime.datetime.now()
    df = pd.DataFrame(monitored_data)
    df.to_csv('lahma_' + str(timestamp) + '.csv')
    total_listeners = sum(df['valid'])
    return total_listeners

if __name__ == '__main__':
    autoFetch(5)
    autoExport(1)

