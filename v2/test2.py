import logging
import pandas as pd
import json
import os
from requests import get
from datetime import datetime, timedelta, timezone
import matplotlib.pyplot as plt


def get_days_usage():
    """"
    This function gets the days kWh usage from Home Assistant
    """
    # Get environment variables
    hass_url = os.environ["HASS_URL"]
    hass_access_token = os.environ["HASS_ACCESS_TOKEN"]

    # Get the current date and time
    current_date = datetime.now()

    # Calculate the beginning of the day
    beginning_of_day = current_date.replace(
        hour=0, minute=0, second=0, microsecond=0)

    # Format the timestamp as per the API spec
    formatted_timestamp = beginning_of_day.strftime(
        '%Y-%m-%dT%H:%M:%S') + "+13:00"

    # Override the timestamp for historical testing
    # formatted_timestamp = "2023-08-04T00:00:00+13:00"

    # formatted_timestamp = "2023-07-31T00:00:00+13:00"

    # The <timestamp> (YYYY-MM-DDThh:mm:ssTZD) is optional and defaults to 1 day before the time of the request. It determines the beginning of the period.
    url = hass_url + "/api/history/period/" + formatted_timestamp

    headers = {
        "Authorization": "Bearer " + hass_access_token,
        "content-type": "application/json",
    }

    parameters = {
        "filter_entity_id": "sensor.house_energy",
        "minimal_response": ""
    }

    print(f"Sending request to {url}")
    response = get(url, params=parameters, headers=headers)
    jsondata = json.loads(response.text)
    print(f"Response code: {response.status_code}")

    with open('raw.json', 'w') as outfile:
        json.dump(jsondata, outfile)

    jsondata = jsondata[0]

    # Remove the first item in the list as it is the current state
    jsondata.pop(0)

    # dump the data to a file for debugging
    with open('data.json', 'w') as outfile:
        json.dump(jsondata, outfile)

    return jsondata


def find_peak_hop(usage):
    """This function finds the peak usage in a valid hour of power"""

    peak_hours = [
        '06:30 AM', '07:00 AM', '07:30 AM', '08:00 AM', '08:30 AM',
        '04:30 PM', '05:00 PM', '05:30 PM', '06:00 PM', '06:30 PM',
        '07:00 PM', '07:30 PM', '08:00 PM', '08:30 PM', '11:30 PM'
    ]

    df = pd.DataFrame(usage)

    # Set state to numeric
    df["state"] = pd.to_numeric(df["state"])

    # Calculate state difference
    df["state_diff"] = df["state"].diff()

    # Calculate the total state difference for the day
    total_kwh = df["state_diff"].sum()

    # Resample data based on 30 minute intervals, where last_changed looks like 2023-08-05T11:00:06.166512+00:00
    # Convert last_changed to a datetime object
    df["datetime"] = pd.to_datetime(df["last_changed"])

    for offset in ['H', '30T']:
        # Resample the data based on the offset and sum the state_diff column
        resampled_df = df.set_index('datetime').resample(
            offset).sum().reset_index()
        resampled_df["strftime"] = resampled_df["datetime"].dt.strftime(
            "%I:%M %p")
        resampled_df = resampled_df[~resampled_df["strftime"].isin(peak_hours)]
        if offset == 'H':
            hour_df = resampled_df
        else:
            halfhour_df = resampled_df

    merged = pd.concat([hour_df, halfhour_df])

    # dump dataframe to a csv file for debugging
    merged.to_csv("merged.csv")

    # Graph the data by 30 minute intervals, color the peak hours red
    # Show the time in NZDT
    plt.figure(figsize=(20, 10))
    plt.bar(merged["strftime"], merged["state_diff"],
            color=merged["strftime"].isin(peak_hours).map({True: 'red', False: 'blue'}))
    plt.xticks(rotation=90)
    plt.title("Power usage by 30 minute intervals")
    plt.xlabel("Time (NZDT)")
    plt.ylabel("kWh")
    plt.tight_layout()

    # save the graph to a file
    plt.savefig("graph.png")

    peak_row = merged.nlargest(1, columns=["state_diff"]).iloc[0]
    kwh = "{:.2f}".format(peak_row["state_diff"])
    time = peak_row["strftime"]

    logging.info(f"{kwh} kWh used at {time}")

    return kwh, time, total_kwh


def main():
    """This function is the main function"""

    # Get the days usage from Home Assistant
    usage = get_days_usage()

    # Change last_changed from UTC to NZDT
    for item in usage:
        item["last_changed"] = datetime.strptime(
            item["last_changed"], '%Y-%m-%dT%H:%M:%S.%f%z').astimezone(timezone(timedelta(hours=13))).strftime('%Y-%m-%dT%H:%M:%S')

    # Dump the data to a file for debugging
    with open('nzdt.json', 'w') as outfile:
        json.dump(usage, outfile)

    # Find the peak hour of power
    peak_kwh, peak_time, total_kwh = find_peak_hop(usage)

    # # Print the results
    print(f"Highest of peak hour {peak_time} with {peak_kwh} kWh used")
    print(f"Total kWh used for the day: {total_kwh:.2f}")


if __name__ == "__main__":
    main()
