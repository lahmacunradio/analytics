''' Importing dependencies
'''
import sys
import os
import requests
from datetime import datetime, timedelta
import time
import threading
import pandas as pd
from dotenv import load_dotenv

''' Importing environment variables ('OUTPUT_PATH', 'API_KEY')
'''
load_dotenv()

''' 
Constants :
    - OUTPUT_PATH           : points to the outputed directory where the CSV file will be saved
    - API_KEY               : personal secret key to access Azuzacast API
    - LONG_LISTENER_THRES   : threshold time delta in minutes above which a listener is considered
                              a "long listener"
    - SHORT_LISTENER_THRES  : threshold time delta in minutes under which a listener is considered
                              a "short listener"
'''
OUTPUT_PATH: str = os.getenv('OUTPUT_PATH')
API_KEY: str = os.getenv('API_KEY')
LONG_LISTENER_THRES: int = 5
SHORT_LISTENER_THRES: int = 1

''' 
Variables :
    - monitored_data    : dictionary containing one row for each listener designated by 'ip', 
                          'location', 'connected_time' and 'valid'. If a listener has at least 
                          one session of more than 'LONG_LISTENER_THRES', they are considered 'valid'.
                          Values are updated at every snapshot.
    - computed_data     : dictionary containing computed values of different count metrics
    - n_hours           : global variable that is overridden by command line argument at script launch
    - launch_time       : time at script launch
'''
monitored_data: dict = {
    'ip': [],
    'location': [],
    'connected_time': [],
    'valid': []
}

computed_data: dict = {
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
launch_time = datetime.now().astimezone()
warning_message = '''--- Enter two integer parameters as shown in example below: 
--- $ python fetcher.py 24
---
--- (above script validates a listener above 5 minutes of listening time,
--- exports and returns total number of valid listeners every 24 hours)'''


# ------------------------------------------------------------------
# Functions
# ------------------------------------------------------------------

def reinitializer() -> None:
    '''
    This method reinitializes the temporary dictionaries used to
    populate the Pandas dataframes that will be outputted in the CSV file.
    '''
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

    launch_time = datetime.now().astimezone()

    print('> reinitializing dataframe')


def snapshot() -> None:
    '''
    This method fetches the Azuracast API and updates 'monitored_data' dictionary above.
    '''

    try:
        global launch_time
        print('> launch time', str(launch_time)[11:19])

        '''
        Connecting to Azuracast API
        '''
        headers: dict = {'Authorization': API_KEY}
        res = requests.get(
            'https://streaming.lahmacun.hu/api/station/1/listeners', headers=headers)

        # print(">>", res.headers['content-type'])
        # exit()
        results = res.json()

        '''
        Initializing 'threshold' time delta in minutes 
        above which a listener is considered a "long listener"
        '''
        threshold = timedelta(minutes=LONG_LISTENER_THRES)

        timestamp = datetime.now().astimezone()
        formatted_timestamp = timestamp.isoformat(sep=' ')
        formatted_timestamp = str(formatted_timestamp)[11:-7]

        for i, listener in enumerate(results):

            connected_time = listener['connected_time']
            connected_time = timedelta(seconds=connected_time)

            connected_time_since_launch = timestamp - launch_time

            ip = listener['ip']

            if listener['location']['status'] == 'error':
                '''
                This handles the case where the API is malfunctioning and returns
                'error' as location status and one or a couple identical IPs for all listeners
                '''
                loc = 'N/A'
                computed_data['valid'][3] += 1
            else:
                loc = listener['location']['country']

            if connected_time > connected_time_since_launch:
                '''
                If listener has been listening since previous monitoring process
                (in other words, in production, since previous day)
                this caps their listening time for the current monitored day
                at the time passed since the current process launch
                '''
                connected_time = connected_time_since_launch

            if ip in monitored_data['ip']:
                '''
                In the case the user is/has been already listening.
                '''
                idx = monitored_data['ip'].index(ip)

                if connected_time >= monitored_data['connected_time'][idx][-1][1]:
                    ''' 
                    In the case the user has been listening since last snapshot.
                    '''
                    monitored_data['connected_time'][idx][-1][1] = connected_time
                    if connected_time > threshold:
                        monitored_data['valid'][idx] = 1
                    elif not monitored_data['valid'][idx] == 1:
                        monitored_data['valid'][idx] = 0
                else:
                    '''
                    In the case the user has started a new listening session.
                    '''
                    monitored_data['connected_time'][idx].append(
                        [formatted_timestamp, connected_time])
                    if connected_time > threshold:
                        monitored_data['valid'][idx] = 1
                    else:
                        monitored_data['valid'][idx] = 0

            else:
                '''
                In the case a new user is detected.
                '''
                monitored_data['ip'].append(ip)
                monitored_data['location'].append(loc)
                monitored_data['connected_time'].append(
                    [[formatted_timestamp, connected_time]])

                if connected_time > threshold:
                    monitored_data['valid'].append(1)
                else:
                    monitored_data['valid'].append(0)

    except Exception as err:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print(f"{type(err)} (line {exc_tb.tb_lineno}) : {err}")


def autoFetch() -> None:
    '''
    This method automates the snapshot() method every 30 seconds.
    '''
    threading.Timer(30.0, autoFetch).start()
    snapshot()


def autoExport() -> None:
    '''
    This method automates the three steps below. 
    1. Converting the 'monitored_data' dictionary to Pandas dataframe 'df_monitored'
    2. Logging following data to 'computed_data' dictionary :
        - Total Listeners       : all IP addresses 
        - Total Long Listeners  : all listeners with at least one session >= 5 min
        - Total Short Listeners : all listeners with session(s) of < 1 min
        - Total N/A Entries     : all listeners with location value at N/A, infering API bug
        - Total Sessions        : all sessions of all listeners
    3. Converting 'computed_data' dictionary to Pandas dataframe 'df_computed'
    4. Appending 'df_computed' to 'df_monitored'
    5. Exporting the resulting 'df' to a CSV file (e.g: lahma_1989-11-09-1111.csv)
    '''

    '''
    Initializing automation timer :
    'n_hours' has been set by command line at script launch.  
    '''
    global n_hours
    threading.Timer(n_hours * 3600.0, autoExport).start()
    timestamp = datetime.now().astimezone()
    time = str(timestamp.time())[:5]
    time = time.replace(':', '')
    date = timestamp.date()

    df_monitored = pd.DataFrame(monitored_data)

    '''
    Populating 'computed_data' dictionary with above mentionned counts.
    Logging Total Listeners
    '''
    computed_data['valid'][0] = len(df_monitored)

    ''' 
    Logging Total Long Listeners
    '''
    total_valid_listeners = sum(df_monitored['valid'])
    computed_data['valid'][1] = total_valid_listeners

    ''' 
    Logging Total Short Listeners
    '''
    computed_data['valid'][2] = 0  # resetting value to 0 before incrementing count
    for entry in df_monitored['connected_time']:
        if (len(entry) == 1 and
                entry[0][1] < timedelta(minutes=SHORT_LISTENER_THRES)
            ):
            computed_data['valid'][2] += 1

    ''' 
    Logging Total N/A Entries
    '''
    computed_data['valid'][3] = 0  # resetting value to 0 before incrementing count
    for entry in df_monitored['location']:
        if entry == 'N/A':
            computed_data['valid'][3] += 1

    ''' 
    Logging Total Sessions
    '''
    computed_data['valid'][4] = 0  # resetting value to 0 before incrementing count
    for entry in df_monitored['connected_time']:
        computed_data['valid'][4] += len(entry)

    '''
    Converting 'computed_data' to Pandas dataframe
    and concatenating it with 'df_monitored' dataframe.
    '''
    df_computed = pd.DataFrame(computed_data)
    df = pd.concat([df_monitored, df_computed])
    df['valid'] = df['valid'].astype('uint16')

    filename = 'lahma_{}_{}.csv'.format(date, time)

    try:
        df.to_csv(OUTPUT_PATH + filename, index=False, sep=';')
        print('> {}: exporting {} in output folder.'.format(
            str(timestamp)[11:19], OUTPUT_PATH + filename))
    except:
        df.to_csv(filename, index=False, sep=';')
        print('> {}: exporting {} in current folder'.format(
            str(timestamp)[11:19], filename))

    reinitializer()


def process_data_fetching(n: float = 24) -> None:
    '''
    Main function that runs the two automated methods above to allow 
    method call with passed arguments through the command line. 
    See ./README.md or command below :
    $ python fetcher.py <n_hours>

    Args:
        n (float) : this method will launch every n hours
    '''

    global n_hours
    n_hours = float(n)
    print('\n{}~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n'.format(
        str(datetime.now().astimezone())[:11]))
    print(f'> script automated every {n_hours*3600} seconds')

    autoFetch()

    time.sleep(n_hours * 3600)
    autoExport()


if __name__ == '__main__':

    if len(sys.argv) != 2:
        print(warning_message)
    else:
        process_data_fetching(float(sys.argv[1]))
