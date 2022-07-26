''' Importing dependencies
'''
import sys
import os
import requests
from datetime import datetime, timedelta
import time
import threading
import pandas as pd
from typing import Dict
from dotenv import load_dotenv

''' Importing environment variables (OUTPUT_PATH, API_KEY)
'''
load_dotenv()

''' Constants
'''
OUTPUT_PATH: str = os.getenv('OUTPUT_PATH')
API_KEY: str = os.getenv('API_KEY')
LONG_LISTENER_MINUTE_THRESHOLD: int = 5
SHORT_LISTENER_MINUTE_THRESHOLD: int = 1

''' Custom types
'''
Vector = Dict[str, list]

''' Variables
'''
monitored_data: Vector = {
    'ip': [],
    'location': [],
    'connected_time': [],
    'valid': []
}

computed_data: Vector = {
    'ip': [
      'Total Listeners', 
      'Total Long Listeners', 
      'Total Short Listeners', 
      'Total N/A entries',
      'Total Sessions'
    ],
    'location': [None, None, None, None, None],
    'connected_time': [None, None, None, None, None],
    'valid': [0, 0, 0, 0, 0]
}

n_hours: float = 24.0
launch_time = datetime.now()

warning_message = '''--- Enter two integer parameters as shown in example below: 
--- $ python fetcher.py 24
---
--- (above script validates a listener above 5 minutes of listening time,
--- exports and returns total number of valid listeners every 24 hours)'''

# ------------------------------------------------------------------
# Functions
# ------------------------------------------------------------------

'''
This method reinitializes the temporary dictionaries used to
populate the Pandas.DataFrame that will be outputted in the csv.
'''
def reinitializer() -> None:
    global monitored_data
    global computed_data
    global launch_time

    monitored_data = {
        'ip': [],
        'location': [],
        'connected_time': [],
        'valid': []
    }

    computed_data = {
        'ip': [
        'Total Listeners', 
        'Total Long Listeners', 
        'Total Short Listeners', 
        'Total N/A entries',
        'Total Sessions'
        ],
        'location': [None, None, None, None, None],
        'connected_time': [None, None, None, None, None],
        'valid': [0, 0, 0, 0, 0]
    }

    launch_time = datetime.now()

    print('> reinitializing dataframe')

def resetTimeDelta():
    pass

'''
This method fetches the Azuracast API and updates 'monitored_data' dictionary above.
An integer is passed as argument representing the minimum minutes threshold
under which a listener is considered 'not valid'.
'''
def snapshot() -> None:

    global launch_time
    print('launch time', str(launch_time)[11:-7])
    headers: dict = {'Authorization': API_KEY}
    res = requests.get('https://streaming.lahmacun.hu/api/station/1/listeners', headers=headers)
    results = res.json()

    threshold = timedelta(minutes=LONG_LISTENER_MINUTE_THRESHOLD)

    timestamp = datetime.now()

    formatted_timestamp = timestamp.isoformat(sep=' ')
    formatted_timestamp = str(formatted_timestamp)[11:-7]

    for i, listener in enumerate(results):

        connected_time = listener['connected_time']
        connected_time = timedelta(seconds=connected_time)

        connected_time_since_launch = timestamp - launch_time

        ip = listener['ip']

        if listener['location']['status'] == 'error':
            '''
            this handles the case where the API is malfunctioning and returns
            'error' as location status and one or a couple identical ips for all listeners
            '''
            loc = 'N/A'
            computed_data['valid'][3] += 1
        else:
            loc = listener['location']['country']

        # if user is/has been already listening
        if ip in monitored_data['ip']:
            i = monitored_data['ip'].index(ip)

            if connected_time > connected_time_since_launch:
                connected_time = connected_time_since_launch

            if connected_time >= monitored_data['connected_time'][i][-1][1]:
                monitored_data['connected_time'][i][-1][1] = connected_time
                if connected_time > threshold:
                    monitored_data['valid'][i] = 1
                else:
                    monitored_data['valid'][i] = 0
            else:
                monitored_data['connected_time'][i].append([formatted_timestamp, connected_time])
                if connected_time > threshold:
                    monitored_data['valid'][i] = 1
                else:
                    monitored_data['valid'][i] = 0

        # if new user is detected
        else:
            monitored_data['ip'].append(ip)
            monitored_data['location'].append(loc)

            if connected_time > connected_time_since_launch:
                connected_time = connected_time_since_launch

            monitored_data['connected_time'].append([[formatted_timestamp, connected_time]])

            if connected_time > threshold:
                monitored_data['valid'].append(1)
            else:
                monitored_data['valid'].append(0)


'''
This method automates the snapshot() method every 30 seconds.
An integer is passed as an argument representing the minimum minutes threshold
under which a listener is considered not 'valid'. If no argument is specified,
the default value is set to 5 minutes.
'''
def autoFetch() -> None:
    threading.Timer(30.0, autoFetch).start()
    snapshot()


'''
This method automates the three steps below every n hours. 
1. Converting the 'monitored_data' dictionary to pandas dataframe 'df_monitored'
2. Logging following data to 'computed_data' dictionary :
    + 'Total Listeners'
    + 'Total Long Listeners'
    + 'Total Short Listeners'
    + 'Total N/A entries'
    + 'Total sessions'
3. Converting 'computed_data' dictionary to pandas dataframe 'df_computed'
4. Appending 'df_computed' to 'df_monitored'
5. Exporting the resulting 'df' to a .csv file (e.g: lahma_1989-11-09-1111.csv)
'''
def autoExport() -> None:
    global n_hours
    threading.Timer(n_hours * 3600.0, autoExport).start()
    timestamp = datetime.now()
    time = str(timestamp.time())[:5]
    time = time.replace(':', '') 
    date = timestamp.date()
    
    df_monitored = pd.DataFrame(monitored_data)

    ''' Logging 'Total Listeners'
    '''
    computed_data['valid'][0] = len(df_monitored)

    ''' Logging 'Total Valid Listeners (more than 5min)
    '''
    total_valid_listeners = sum(df_monitored['valid'])
    computed_data['valid'][1] = total_valid_listeners

    ''' Logging 'Total Short Listeners' (less than 60s)
    '''
    computed_data['valid'][2] = 0
    for entry in df_monitored['connected_time']:
        if (len(entry) == 1 and 
            entry[0][1] < timedelta(minutes=SHORT_LISTENER_MINUTE_THRESHOLD)
            ):
            computed_data['valid'][2] += 1

    ''' Logging 'Total N/A Entries'
    '''
    computed_data['valid'][3] = 0
    for entry in df_monitored['location']:
        if entry == 'N/A':
            computed_data['valid'][3] += 1

    ''' Logging 'Total Listening Sessions'
    '''
    computed_data['valid'][4] = 0
    for entry in df_monitored['connected_time']:
        computed_data['valid'][4] += len(entry)

    df_computed = pd.DataFrame(computed_data)

    df = pd.concat([df_monitored, df_computed])
    df['valid'] = df['valid'].astype('uint16')

    filename = 'lahma_{}_{}.csv'.format(date, time)

    try:
        df.to_csv(OUTPUT_PATH + filename, index=False, sep =';')
        print('{}: exporting {} in output folder.'.format(str(timestamp)[11:-7], OUTPUT_PATH + filename))
    except:
        df.to_csv(filename, index=False, sep =';')
        print('{}: exporting {} in current folder'.format(str(timestamp)[11:-7], filename))

    reinitializer()


'''
This method aggregates the two automated methods above to allow 
method call with passed arguments through the command line. Format below :
$ python API_autoFetcher.py <minutes_threshold> <n_hours>
'''
def automate(n: float = 24) -> None:

    global n_hours
    n_hours = float(n)
    print('\n{}~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n'.format(str(datetime.now())[:11]))
    print(f'\t- script automated every {n_hours*3600} seconds')

    autoFetch()
    
    time.sleep(n_hours * 3600)
    autoExport()

if __name__ == '__main__':

    if len(sys.argv) != 2:
        print(warning_message)
    else:
        automate(float(sys.argv[1]))