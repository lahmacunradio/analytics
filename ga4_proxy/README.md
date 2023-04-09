# GA4 Proxy

## Objective

Create new endpoint on arcsi or sauce (arcsi may be overloaded and/or the radio stats are not necessarily arcsi scope) to which the app can send listeners stats.

## Dependencies

### 1. Create a virtual environment :

- on Linux/Mac OS:

        python3 -m venv venv

- on Windows:

        python -m venv venv

### 2. Activate the virtual environment :

- on Linux/Mac OS :

        source venv/bin/activate

- on Windows :

        venv/Scripts/activate

### 3. Install the necessary librairies :

    pip install -r requirements.txt

## Usage

Launch Flask server :

    $ flask run

Send POST requests to GA4 API :

- Endpoint :

        http://127.0.0.1:5000/ga4_proxy

- Data format :

        {
            "show_title": "transverszia",
            "show_subtitle": "don't be sorry be careful",
            "event_type": "Radio play"
        }
