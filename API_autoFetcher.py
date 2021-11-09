import requests
import datetime
import threading
import pandas as pd
import sys


'''
Create and import custom module 'access.py' to access your own API token and log in.
See 'access_template.py' for template.
'''
import access
API_KEY = access.MY_KEY


monitored_data = {
    'ip': [],
    'location': [],
    'connected_time': [],
    'valid': []
}

global n_hours


'''
This method fetches the Azuracast API and updates 'monitored_data' dictionary above.
An integer is passed as argument representing the minimum minutes threshold
under which a listener is considered not 'valid'.
'''
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
            # this handles the case where the API is malfunctioning and returns
            # 'error' as location status and identical 'ip' for all listeners
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

    timestamp = datetime.datetime.now()
    time = timestamp.time()
    print('snapshot at ' + str(time)[:8])


'''
This method automates the snapshot() method every 30 seconds.
An integer is passed as argument representing the minimum minutes threshold
under which a listener is considered not 'valid'. If no argument is specified,
the default value is set to 5 minutes.
'''
def autoFetch(minutes_threshold = 5):
    threading.Timer(30.0, autoFetch).start()
    snapshot(minutes_threshold)


'''
This method automates the three steps below every n hours. 
1. Converting the 'monitored_data' dictionary to a pandas dataframe
2. Exporting the df in question to a .csv file (e.g: lahma_1989-11-09.csv)
3. Returning 'total_listeners' (nbr of valid listeners) during the monitored time frame
'''
def autoExport():
    global n_hours
    threading.Timer(n_hours * 3600.0, autoExport).start()
    timestamp = datetime.datetime.now()
    time = timestamp.time()
    date = timestamp.date()
    df = pd.DataFrame(monitored_data)
    df.to_csv('lahma_' + str(date) + '.csv')
    total_listeners = sum(df['valid'])
    print('export at', str(time)[:8], '| total listeners:', str(total_listeners))
    return total_listeners


'''
This method aggregates the two automated methods above to allow 
method call with passed arguments through the command line. Format below :
$ python API_autoFetcher.py <minutes_threshold> <n_hours>
'''
def automate(minutes_threshold, n):

    autoFetch(float(minutes_threshold))

    global n_hours
    n_hours = float(n)
    autoExport()


if __name__ == '__main__':

    if len(sys.argv) != 3:
        print('''------ Enter two integer parameters as shown in example below: 
------ $ python API_autoFetcher.py 5 24
------
------ (above script validates a listener above 5 minutes of listening time,
------ exports and returns total number of valid listeners every 24 hours)''')
    else:
        automate(sys.argv[1], sys.argv[2])