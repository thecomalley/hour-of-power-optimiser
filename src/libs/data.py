import pandas as pd
import logging


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
    
    # remove all peak rows as we are only interested in off peak
    df = df[df['time_period'] != 'peak']
    
    # ensure state is numeric
    df['state'] = pd.to_numeric(df['state'])

    # Calculate cost for each row
    df['cost'] = df['state'] * df['time_period'].map(rates)
    
    df.to_csv('find_optimal_hop.csv')
    

    # Ensure 'cost' is numeric
    df['cost'] = pd.to_numeric(df['cost'], errors='coerce')
    
    # Resample into 1-hour and 30-minute intervals and calculate cost for each interval
    cost_by_hour = df.resample('1H').sum()['cost']
    cost_by_half_hour = df.resample('30T').sum()['cost']

    # Find interval with highest cost
    optimal_hour = cost_by_hour.idxmax()
    optimal_half_hour = cost_by_half_hour.idxmax()

    # If the highest cost is in the 1-hour interval, use that
    if cost_by_hour[optimal_hour] > cost_by_half_hour[optimal_half_hour]:
        optimal_time_period = optimal_hour
        total_kwh = df[df.index.hour == optimal_hour.hour]['state'].sum()
    else:
        # If the highest cost is in the 30-minute interval, use that
        optimal_time_period = optimal_half_hour
        total_kwh = df[(df.index.hour == optimal_half_hour.hour) &
                       (df.index.minute == optimal_half_hour.minute)]['state'].sum()

    # Convert optimal_time_period to 12-hour format for logging & notifications
    start_time = optimal_time_period.strftime("%I:%M %p")
    end_time = (optimal_time_period +
                pd.Timedelta(minutes=60)).strftime("%I:%M %p")

    # dump to csv for debugging
    # df.to_csv('find_optimal_hop.csv')

    # To calculate cost we need to know what rate we are on
    if optimal_time_period.hour >= 9 and optimal_time_period.hour < 17:  # Off Peak Shoulder
        cost = total_kwh * rates['off_peak_shoulder']
    elif optimal_time_period.hour >= 21 and optimal_time_period.hour < 23:  # Off Peak Shoulder
        cost = total_kwh * rates['off_peak_shoulder']
    elif optimal_time_period.hour >= 23 or optimal_time_period.hour < 7:  # Off Peak
        cost = total_kwh * rates['off_peak']

    logging.info(f"Optimal time period: {start_time} - {end_time}")
    logging.info(f"Total kWh: {total_kwh}")
    logging.info(f"Cost: ${cost}")

    return total_kwh, start_time, cost

