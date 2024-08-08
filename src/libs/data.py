import pandas as pd
import logging

def find_optimal_hop(usage):
    """
    This function returns the optimal hop time and the kWh used.
    """
    # Define rates
    rates = {
        'off_peak_shoulder': 0.1852,
        'off_peak': 0.1323
    }

    # Load data into pandas dataframe
    df = pd.DataFrame(usage)

    # Process timestamps
    df["timestamp"] = pd.to_datetime(df["last_changed"]).dt.tz_convert(tz="Pacific/Auckland")
    df["strftime"] = df["timestamp"].dt.strftime("%I:%M %p")

    # Set state to numeric and calculate state difference
    df["state"] = pd.to_numeric(df["state"]).diff()

    # Resample data into 30-minute intervals
    df = df.set_index('timestamp').resample('30T', origin='start_day').sum()

    # Define time periods
    time_periods = [
        ((7, 9), 'peak'),
        ((17, 21), 'peak'),
        ((9, 17), 'off_peak_shoulder'),
        ((21, 23), 'off_peak_shoulder'),
        ((23, 7), 'off_peak')
    ]

    # Assign time periods
    for (start, end), period in time_periods:
        if start < end:
            df.loc[(df.index.hour >= start) & (df.index.hour < end), 'time_period'] = period
        else:
            df.loc[(df.index.hour >= start) | (df.index.hour < end), 'time_period'] = period

    # Filter out peak periods
    df = df[df['time_period'] != 'peak']

    # Calculate cost
    df['cost'] = df['state'] * df['time_period'].map(rates)

    # Ensure 'cost' is numeric
    df['cost'] = pd.to_numeric(df['cost'], errors='coerce')

    # Resample and calculate cost for each interval
    cost_by_hour = df.resample('1H').sum()['cost']
    cost_by_half_hour = df.resample('30T').sum()['cost']

    # Find optimal time period
    optimal_hour = cost_by_hour.idxmax()
    optimal_half_hour = cost_by_half_hour.idxmax()

    # Determine the optimal time period and total kWh
    if cost_by_hour[optimal_hour] >= cost_by_half_hour[optimal_half_hour]:
        optimal_time_period = optimal_hour
        total_kwh = df[df.index.hour == optimal_hour.hour]['state'].sum()
    else:
        optimal_time_period = optimal_half_hour
        total_kwh = df[(df.index.hour == optimal_half_hour.hour) & 
                       (df.index.minute == optimal_half_hour.minute)]['state'].sum()

    # Format optimal time period for logging
    start_time = optimal_time_period.strftime("%I:%M %p")
    end_time = (optimal_time_period + pd.Timedelta(minutes=60)).strftime("%I:%M %p")

    # Determine cost based on time period
    if 9 <= optimal_time_period.hour < 17 or 21 <= optimal_time_period.hour < 23:
        cost = total_kwh * rates['off_peak_shoulder']
    else:
        cost = total_kwh * rates['off_peak']

    total_kwh = round(total_kwh, 2)
    cost = round(cost, 2)
    
    logging.info(f"Hour of Power: {start_time} - {end_time}")
    logging.info(f"Total kWh: {total_kwh}")
    logging.info(f"Estimated Savings: ${cost}")

    return start_time, end_time, total_kwh, cost