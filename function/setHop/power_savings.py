import json
from requests import get, post
import os

import pandas as pd

from ElectricKiwi.electrickiwi import ElectricKiwi, hop_score

def get_days_usage():
    """"
    This function gets the days kWh usage from Home Assistant
    """
    # Get environment variables
    hass_url = os.environ["HASS_URL"]
    hass_access_token = os.environ["HASS_ACCESS_TOKEN"]

    # The <timestamp> (YYYY-MM-DDThh:mm:ssTZD) is optional and defaults to 1 day before the time of the request. It determines the beginning of the period.
    url = hass_url + "/api/history/period"

    headers = {
        "Authorization": "Bearer " + hass_access_token,
        "content-type": "application/json",
    }
    parameters = {
        "filter_entity_id": "sensor.house_energy",
        "minimal_response": ""
    }

    response = get(url, params=parameters, headers=headers)
    jsondata = json.loads(response.text)
    jsondata = jsondata[0]

    return jsondata

def find_peak_hop(usage):
    """This function finds the peak usage in a valid hour of power"""

    # Set list of invalid hop hours
    peak_hours = ['06:30 AM',
                  '07:00 AM',
                  '07:30 AM',
                  '08:00 AM',
                  '08:30 AM',
                  '04:30 PM',
                  '05:00 PM',
                  '05:30 PM',
                  '06:00 PM',
                  '06:30 PM',
                  '07:00 PM',
                  '07:30 PM',
                  '08:00 PM',
                  '08:30 PM'
                  '11:30 PM']

    # Load data into pandas datafrAMe
    df = pd.DataFrame(usage)

    # add new datetime column based on last_changed
    df["datetime"] = pd.to_datetime(df["last_changed"])

    # Change Timzone to NZDT
    df["datetime"] = df["datetime"].dt.tz_convert(tz="Pacific/Auckland")

    # Drop unused columns
    df = df.drop(columns=["entity_id", "attributes",
                          "last_updated", "last_changed"])

    # Set state to numeric
    df["state"] = pd.to_numeric(df["state"])

    # run diff on state
    df["state"] = df["state"].diff()

    hour = df.set_index('datetime').resample('H', origin='start_day',).sum()
    hour = hour.reset_index()
    hour["strftime"] = hour["datetime"].dt.strftime("%I:%M %p")
    hour = hour.query("strftime != @peak_hours")

    halfhour = df.set_index('datetime').resample(
        'H', offset="30T", origin='start_day').sum()
    halfhour = halfhour.reset_index()
    halfhour["strftime"] = halfhour["datetime"].dt.strftime("%I:%M %p")
    halfhour = halfhour.query("strftime != @peak_hours")

    datafrAMes = [hour, halfhour]
    merged = pd.concat(datafrAMes)
    # print(merged)

    max = merged.nlargest(1, columns=["state"])
    kwh = max.iat[0, 1]
    kwh = "{:.2f}".format(kwh)
    time = max.iat[0, 2]

    print(f"{kwh}kWh used at {time}")

    return kwh, time

def set_hop(hop):
    """"
    This function sets the HOP using the Electric Kiwi API
    """
    # Get environment variables
    ek_email = os.environ["EK_EMAIL"]
    ek_password = os.environ["EK_PASSWORD"]
    
    # build a list of all posible HOPs (has got to be a better way...) so we can pass index # to the API
    ek_hours = ['12:00 AM',
                '12:30 AM',
                '01:00 AM',
                '01:30 AM',
                '02:00 AM',
                '02:30 AM',
                '03:00 AM',
                '03:30 AM',
                '04:00 AM',
                '04:30 AM',
                '05:00 AM',
                '05:30 AM',
                '06:00 AM',
                '06:30 AM',
                '07:00 AM',
                '07:30 AM',
                '08:00 AM',
                '08:30 AM',
                '09:00 AM',
                '09:30 AM',
                '10:00 AM',
                '10:30 AM',
                '11:00 AM',
                '11:30 AM',
                '12:00 PM',
                '12:30 PM',
                '01:00 PM',
                '01:30 PM',
                '02:00 PM', 
                '02:30 PM', 
                '03:00 PM', 
                '03:30 PM', 
                '04:00 PM', 
                '04:30 PM', 
                '05:00 PM', 
                '05:30 PM', 
                '06:00 PM', 
                '06:30 PM', 
                '07:00 PM', 
                '07:30 PM', 
                '08:00 PM', 
                '08:30 PM', 
                '09:00 PM', 
                '09:30 PM', 
                '10:00 PM', 
                '10:30 PM', 
                '11:00 PM', 
                '11:30 PM']

    # Get the index of the time period we want to set as the hop
    hop_hour = ek_hours.index(hop)+1

    ek = ElectricKiwi()
    token = ek.at_token()

    customer = ek.login(ek_email, ek.password_hash(ek_password))
    print('Logged in: OK')

    print(f"setting HOP to {hop}")
    ek.set_hop_hour(hop_hour)

    get_hop = ek.get_hop_hour()
    print(f"hop set to {get_hop}")

    return get_hop

def notify_hass(state, attributes):
    """"
    This function updates a sensor in Home Assistant
    """
    # Get environment variables
    hass_url = os.environ["HASS_URL"]
    hass_access_token = os.environ["HASS_ACCESS_TOKEN"]

    # The <timestamp> (YYYY-MM-DDThh:mm:ssTZD) is optional and defaults to 1 day before the time of the request. It determines the beginning of the period.
    url = hass_url + "/api/states/sensor.ek_hop"
    
    headers = {
        "Authorization": "Bearer " + hass_access_token,
        "content-type": "application/json",
    }

    payload = {
        "state": state,
        "attributes": attributes
    }

    response = post(url, data=json.dumps(payload), headers=headers)
    print(response.text)
