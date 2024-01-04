import json
import logging

from requests import get, post
import os
from decimal import Decimal
import arrow

import pandas as pd

from ElectricKiwi.electrickiwi import ElectricKiwi, hop_score


def get_days_usage():
    """"
    This function gets the days kWh usage from Home Assistant
    """
    # Get environment variables
    hass_url = os.environ["HASS_URL"]
    hass_access_token = os.environ["HASS_ACCESS_TOKEN"]

    # The <timestamp> (YYYY-MM-DDThh:mm:ssTZD) is optional and defaults to 1 day before the time of the request.
    # It determines the beginning of the period.
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
    """This function finds the peak usage in a valid hour of power and returns the hour of power and the kWh used"""
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

    # Load data into pandas dataframe
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
    # logging.info(merged)

    # dump to csv for debugging
    merged.to_csv('find_peak_hop.csv')

    max = merged.nlargest(1, columns=["state"])
    kwh = max.iat[0, 1]
    kwh = "{:.2f}".format(kwh)
    time = max.iat[0, 2]

    logging.info(f"{kwh}kWh used at {time}")

    return kwh, time


def find_optimal_hop(usage):
    """
    This function returns the optimal hop time and the kWh used
    """
    # Define rates
    rates = {
        'off_peak_shoulder': 0.1852,
        'off_peak': 0.1323
    }

    # Load data into pandas dataframe
    df = pd.DataFrame(usage)

    # add new datetime column based on last_changed
    df["timestamp"] = pd.to_datetime(df["last_changed"])

    # Change Timzone to NZDT
    df["timestamp"] = df["timestamp"].dt.tz_convert(tz="Pacific/Auckland")

    # Add a column for the time in 12-hour format
    df["strftime"] = df["timestamp"].dt.strftime("%I:%M %p")

    # Drop unused columns
    df = df.drop(columns=["entity_id", "attributes",
                          "last_updated", "last_changed"])

    # Set state to numeric
    df["state"] = pd.to_numeric(df["state"])

    # run diff on state
    df["state"] = df["state"].diff()

    # Order the data into 30 minute intervals starting at 00:00
    df = df.set_index('timestamp').resample('30T', origin='start_day').sum()

    # If time period is between 7am and 9am, set time_period column to peak
    df.loc[(df.index.hour >= 7) & (df.index.hour < 9),
           'time_period'] = 'peak'

    # If time period is between 5pm and 9pm, set time_period column to peak
    df.loc[(df.index.hour >= 17) & (df.index.hour < 21),
           'time_period'] = 'peak'

    # If time period is between 9am and 5pm, set time_period column to off_peak_shoulder
    df.loc[(df.index.hour >= 9) & (df.index.hour < 17),
           'time_period'] = 'off_peak_shoulder'

    # If time period is between 9pm and 11pm, set time_period column to off_peak_shoulder
    df.loc[(df.index.hour >= 21) & (df.index.hour < 23),
           'time_period'] = 'off_peak_shoulder'

    # If time period is between 11pm and 7am, set time_period column to off_peak
    df.loc[(df.index.hour >= 23) | (df.index.hour < 7),
           'time_period'] = 'off_peak'

    # Calculate cost for each row
    df['cost'] = df['state'] * df['time_period'].map(rates)

    # Resample into 1-hour and 30-minute intervals and calculate cost for each interval
    cost_by_hour = df.resample('1H').sum()['cost']
    cost_by_half_hour = df.resample('30T').sum()['cost']

    # Find interval with highest cost
    optimal_hour = cost_by_hour.idxmax()
    optimal_half_hour = cost_by_half_hour.idxmax()

    if cost_by_hour[optimal_hour] > cost_by_half_hour[optimal_half_hour]:
        optimal_time_period = optimal_hour
        total_kwh = df[df.index.hour == optimal_hour.hour]['state'].sum()
    else:
        optimal_time_period = optimal_half_hour
        total_kwh = df[(df.index.hour == optimal_half_hour.hour) &
                       (df.index.minute == optimal_half_hour.minute)]['state'].sum()

    cost = df[(df.index.hour == optimal_time_period.hour) &
              (df.index.minute == optimal_time_period.minute)]['cost'].sum()

    start_time = optimal_time_period.strftime("%I:%M %p")
    end_time = (optimal_time_period +
                pd.Timedelta(minutes=60)).strftime("%I:%M %p")

    # dump to csv for debugging
    df.to_csv('find_optimal_hop.csv')

    logging.info(f"Optimal time period: {start_time} - {end_time}")
    logging.info(f"Total kWh: {total_kwh}")
    logging.info(f"Cost: ${cost}")

    return total_kwh, start_time, cost


def set_hop(hop):
    """"
    This function sets the HOP using the Electric Kiwi API
    """
    try:
        # Get environment variables
        ek_email = os.environ["EK_EMAIL"]
        ek_password = os.environ["EK_PASSWORD"]

        # build a list of all possible HOPs (has got to be a better way...) so we can pass index # to the API
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
                    '11:30 PM'
                    ]

        # Get the index of the time period we want to set as the hop
        hop_hour = ek_hours.index(hop)+1

        ek = ElectricKiwi()
        token = ek.at_token()
        ek.login(ek_email, ek.password_hash(ek_password))
        logging.info('Logged in: OK')

        ek.set_hop_hour(hop_hour)
        hop_hour = ek.get_hop_hour()

    except Exception as e:
        logging.error(f"Failed to set Hour of Power to {hop}")
        logging.exception(e)
        return False

    else:
        logging.info(f"Set Hour of Power to to {hop_hour}")
        return hop_hour


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
    logging.info(response.text)


def get_last_days_usage() -> None:
    # Get environment variables
    ek_email = os.environ["EK_EMAIL"]
    ek_password = os.environ["EK_PASSWORD"]

    ek = ElectricKiwi()
    token = ek.at_token()

    customer = ek.login(ek_email, ek.password_hash(ek_password))

    connection = ek.connection_details()

    kwh_cost = Decimal(connection['pricing_plan']['usage_rate_inc_gst'])
    wrong_kwh = Decimal('0.0')
    hop_savings = Decimal('0.0')

    logging.info("")
    consumption = ek.consumption(arrow.now().shift(days=-2), arrow.now())
    for date in consumption:
        data = consumption[date]

        hop_usage = Decimal(data['consumption_adjustment'])
        hop_savings += hop_usage
        hop_best_hour = []

        for interval in range(1, 24*2):
            interval_data = data['intervals'][str(interval)]
            if interval_data['hop_best']:
                hop_best = Decimal(interval_data['consumption']) + Decimal(
                    data['intervals'][str(interval+1)]['consumption'])
                hop_best_hour.append(interval_data['time'])
                break

        date = arrow.get(date, 'YYYY-MM-DD').format('DD/MM/YYYY')

        diff = hop_best - hop_usage

        yesterday = {
            "date": date,
            "usage_best": str(hop_best),
            "hour_best": hop_best_hour[0],
            "usage_actual": str(hop_usage),
            "hour_actual": "??",
            "savings_actual": "${:.2f}".format(hop_savings * kwh_cost),
            "savings_best": "${:.2f}".format(hop_savings * kwh_cost)
        }

        return yesterday

        if diff > 0.01:
            wrong_kwh += diff
            hop_savings * kwh_cost
            return f"{date}: Wrong HOP: {hop_usage} @ ?? vs {hop_best} @ {hop_best_hour} - ${hop_savings * kwh_cost}"
            logging.info('{} - Wrong HOP: {}kWh ({}) vs {}kWh ({}kWh)'.format(date,
                         hop_best, hop_best_hour, hop_usage, diff))
        else:
            return f"{date}: Correct HOP: {hop_best} @ {hop_best_hour}"
            logging.info('{} - Correct HOP: {}kWh'.format(date, hop_usage))

    logging.info('\nHOP Savings: {}kWh (${:.2f})'.format(
        hop_savings, hop_savings * kwh_cost))
    logging.info('Missed HOP: {}kWh (${:.2f})'.format(
        wrong_kwh, wrong_kwh * kwh_cost))
    logging.info('HOP Score: {:.2f}%'.format(
        Decimal(100.0) - ((wrong_kwh / hop_savings) * 100)))
