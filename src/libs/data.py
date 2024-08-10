import pandas as pd
import logging
from datetime import datetime, timedelta
import pytz


def calculate_peak_usage(data):
    # Define the UTC and NZDT timezones
    nzdt = pytz.timezone('Pacific/Auckland')

    # Define peak hours that cannot be set as 'hour of free power'
    peak_hours = [
        '06:30 AM', '07:00 AM', '07:30 AM', '08:00 AM', '08:30 AM',
        '04:30 PM', '05:00 PM', '05:30 PM', '06:00 PM', '06:30 PM',
        '07:00 PM', '07:30 PM', '08:00 PM', '08:30 PM', '11:30 PM'
    ]
    peak_hours = [datetime.strptime(hour, "%I:%M %p").time()
                  for hour in peak_hours]

    # Convert data into a DataFrame
    df = pd.DataFrame(data)

    # Convert timestamps to datetime objects and state to floats
    df['last_changed'] = pd.to_datetime(
        df['last_changed'], utc=True)  # Set as UTC
    df['state'] = df['state'].astype(float)

    # Convert all timestamps from UTC to NZDT
    df['last_changed'] = df['last_changed'].dt.tz_convert(nzdt)

    # Calculate power usage over 60-minute intervals starting at 30-minute marks
    def calculate_60min_intervals(df):
        intervals = []
        # Generate 60-minute intervals starting at 30-minute marks
        start_time = df['last_changed'].min().floor('h') + \
            timedelta(minutes=30)
        end_time = df['last_changed'].max().ceil('h')

        current_time = start_time
        while current_time <= end_time - timedelta(hours=1):
            next_time = current_time + timedelta(hours=1)
            interval_data = df[(df['last_changed'] >= current_time) & (
                df['last_changed'] < next_time)]
            if not interval_data.empty:
                power_used = interval_data['state'].max(
                ) - interval_data['state'].min()
                intervals.append((current_time, next_time, power_used))
            current_time += timedelta(minutes=30)

        return intervals

    # Calculate power usage for all 60-minute intervals starting at 30-minute marks
    intervals = calculate_60min_intervals(df)

    # Filter out intervals that overlap with peak hours
    def overlaps_peak_hours(start, end):
        for peak_time in peak_hours:
            if start.time() <= peak_time < end.time() or start.time() < peak_time <= end.time():
                return True
        return False

    filtered_intervals = [
        (start, end, usage) for start, end, usage in intervals
        if not overlaps_peak_hours(start, end)
    ]

    # Find the interval with the maximum usage
    if filtered_intervals:
        max_interval = max(filtered_intervals, key=lambda x: x[2])
        max_usage_start, max_usage_end, max_usage_value = max_interval

        # Format for the upstream
        simple_start_time = max_usage_start.strftime("%I:%M %p")
        simple_end_time = max_usage_end.strftime("%I:%M %p")
        max_usage_value = round(max_usage_value, 2)

        # Output the result
        logging.info(
            f"The 60-minute interval with the most power usage is from {max_usage_start} to {max_usage_end} NZDT")
        logging.info(f"Power used during this interval: {max_usage_value} kWh")
        logging.info(f"Formatted start time for API: {simple_start_time}")

        # Return the formatted start time for further use if needed
        return simple_start_time, simple_end_time, max_usage_value
    else:
        logging.info("No valid intervals found.")
        return None
