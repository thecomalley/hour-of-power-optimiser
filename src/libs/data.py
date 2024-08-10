import matplotlib.pyplot as plt
import matplotlib
import logging
import pandas as pd
import logging
from datetime import timedelta
import pytz
matplotlib.use('Agg')  # Set the backend to 'Agg'


def calculate_optimal_hop(data):
    # Define the UTC and NZDT timezones
    utc = pytz.utc
    nzdt = pytz.timezone('Pacific/Auckland')

    # Define the rates per kWh
    peak_rate = 0.2208  # Peak time
    shoulder_rate = 0.1546  # Off-peak shoulder time
    night_rate = 0.1104  # Off-peak night time

    # Peak hours that cannot be the start of an interval
    peak_hours = ['06:30 AM', '07:00 AM', '07:30 AM', '08:00 AM', '08:30 AM',
                  '04:30 PM', '05:00 PM', '05:30 PM', '06:00 PM', '06:30 PM',
                  '07:00 PM', '07:30 PM', '08:00 PM', '08:30 PM', '11:30 PM']

    # Convert data into a DataFrame
    df = pd.DataFrame(data)

    # Convert timestamps to datetime objects and state to floats
    df['last_changed'] = pd.to_datetime(
        df['last_changed'], utc=True)  # Set as UTC
    df['state'] = df['state'].astype(float)

    # Convert all timestamps from UTC to NZDT
    df['last_changed'] = df['last_changed'].dt.tz_convert(nzdt)

    # Function to determine the rate based on time of day
    def get_rate(timestamp):
        hour = timestamp.hour
        weekday = timestamp.weekday()

        # Peak time (Weekdays 7am-9am and 5pm-9pm)
        if weekday < 5 and ((7 <= hour < 9) or (17 <= hour < 21)):
            return peak_rate
        # Off-peak shoulder (Weekdays 9am-5pm, 9pm-11pm; Weekends 7am-11pm)
        elif (weekday < 5 and (9 <= hour < 17 or 21 <= hour < 23)) or (weekday >= 5 and (7 <= hour < 23)):
            return shoulder_rate
        # Off-peak night (11pm-7am daily)
        else:
            return night_rate

    # Check if an interval falls entirely within off-peak shoulder or off-peak night times only
    def is_off_peak_time(start, end):
        return get_rate(start) != peak_rate and get_rate(end - timedelta(minutes=1)) != peak_rate

    # Calculate power usage over 60-minute intervals starting at 30-minute marks
    def calculate_60min_intervals(df):
        intervals = []
        # Generate 60-minute intervals starting at 30-minute marks
        start_time = df['last_changed'].min().floor('H') + \
            timedelta(minutes=30)
        end_time = df['last_changed'].max().ceil('H')

        current_time = start_time
        while current_time <= end_time - timedelta(hours=1):
            next_time = current_time + timedelta(hours=1)
            # Ensure the start time is not in the list of peak hours
            if current_time.strftime("%I:%M %p") not in peak_hours:
                interval_data = df[(df['last_changed'] >= current_time) & (
                    df['last_changed'] < next_time)]
                if not interval_data.empty:
                    power_used = interval_data['state'].max(
                    ) - interval_data['state'].min()
                    # Calculate the total cost for the interval based on rate at start time
                    rate = get_rate(current_time)
                    total_cost = power_used * rate
                    if is_off_peak_time(current_time, next_time):
                        intervals.append(
                            (current_time, next_time, total_cost, power_used))
            current_time += timedelta(minutes=30)

        return intervals

    # Calculate power usage and cost for all 60-minute intervals starting at 30-minute marks
    intervals = calculate_60min_intervals(df)

    # Find the interval with the maximum cost
    if intervals:
        max_interval = max(intervals, key=lambda x: x[2])
        max_usage_start, max_usage_end, max_usage_cost, max_usage_kwh = max_interval

        # Format the start and end times for the Power Company API
        simple_start_time = max_usage_start.strftime("%I:%M %p")
        simple_end_time = max_usage_end.strftime("%I:%M %p")

        # Round cost and kWh to two decimal places
        max_usage_cost = round(max_usage_cost, 2)
        max_usage_kwh = round(max_usage_kwh, 2)

        # Output the result
        logging.info(
            f"The 60-minute interval with the highest cost is from {max_usage_start} to {max_usage_end} NZDT")
        logging.info(
            f"Cost during this interval: {max_usage_cost} currency units")
        logging.info(f"Power used during this interval: {max_usage_kwh} kWh")
        logging.info(f"Formatted start time for API: {simple_start_time}")
        logging.info(f"Formatted end time for API: {simple_end_time}")

        # Return the formatted start time, end time, cost, and kWh for further use if needed
        return simple_start_time, simple_end_time, max_usage_cost, max_usage_kwh, intervals
    else:
        logging.info("No valid intervals found.")
        return None


def plot_intervals(intervals, filename='intervals_plot.png'):
    """
    Plots the intervals and their associated costs, and saves the plot to a PNG file.

    :param intervals: List of tuples containing interval start time, end time, cost, and power used.
                      Example: [(start_time, end_time, cost, kWh), ...]
    :param filename: Name of the file to save the plot to. Default is 'intervals_plot.png'.
    """
    if not intervals:
        print("No intervals to plot.")
        return

    # Extract data for plotting
    start_times = [interval[0] for interval in intervals]
    end_times = [interval[1] for interval in intervals]
    costs = [interval[2] for interval in intervals]
    kwhs = [interval[3] for interval in intervals]

    # Create a figure and axis
    fig, ax1 = plt.subplots(figsize=(12, 8))

    # Bar chart for costs
    bars = ax1.barh(range(len(intervals)), costs,
                    color='skyblue', edgecolor='black')
    ax1.set_xlabel('Cost (currency units)')
    ax1.set_ylabel('Intervals')
    ax1.set_yticks(range(len(intervals)))
    ax1.set_yticklabels(
        [f'{start.strftime("%I:%M %p")} - {end.strftime("%I:%M %p")}' for start, end in zip(start_times, end_times)])
    ax1.set_title('Cost of 60-minute Intervals')

    # Adding value labels on the bars
    for bar in bars:
        width = bar.get_width()
        ax1.text(width + 0.01, bar.get_y() + bar.get_height() / 2,
                 f'{width:.2f}', va='center', ha='left')

    # Save the plot to a PNG file
    plt.tight_layout()
    plt.savefig(filename, format='png')
    print(f"Plot saved to {filename}")
