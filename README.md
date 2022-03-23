# Lahmacun Radio Analytics

<img width="408" alt="lahma" src="https://user-images.githubusercontent.com/84317349/139689563-4ab78163-26f0-4a4c-a745-847eecfbfd55.png">

Contributions to Lahmacun Radio analytics team.<br>
Lahmacun is a community music webradio based in Budapest.

## Objectives:
1. Get number of unique listeners per day:
    + fetch AzuraCast API
    + store relevant data in a Python dictionary
    + automate API snapshot twice every minute to update dictionary
    + automate export to csv (or parquet ? feather?) + return of total valid listeners every n hours
2. Get total listened time per show per week

## Dependencies:

### 1. Create a virtual environment : 
+ on Linux/Mac OS: 

        python3 -m venv virtual
+ on Windows:

        python -m venv virtual
        
### 2. Activate the virtual environment :
+ on Linux/Mac OS : 
        
        source virtual/bin/activate
+ on Windows :

        virtual/Scripts/activate
        
### 3. Install the necessary librairies :

        pip install -r requirements.txt

## Usage:
Methods from *API_autoFetcher.py* can be called through the command line, like so:

    $ python fetcher.py <n_hours>

**<n_hours>** : determines the occurrences of exports (in hours).

## Details on outputted csv file :

In [example.csv](/example.csv), the first two fields 'ip' and 'location' are self-explanatory. The third field 'connected_time' is populated by arrays of one or more arrays. If there are indeed several arrays, this means the corresponding user has connected several times to the broadcast. NB: by *connected*, we mean pressing play until pressing pause or closing tab.

Each array contains 2 time values (in python module *datetime* format):
+ timestamp of connection
+ connection time (in seconds)

        [[datetime.datetime(2021, 10, 14, 12, 23, 58, 464265), datetime.timedelta(seconds=31261)], 
        [datetime.datetime(2021, 10, 14, 12, 58, 48, 479164), datetime.timedelta(seconds=79463)]]
        
In the example above, the user has first connected to the broadcast on *Oct 14, 2021 at 12:23:58* for *31261 seconds*, and a little later at *12:58:48* for *79463* seconds.

