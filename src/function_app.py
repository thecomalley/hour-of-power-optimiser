import logging
import os
import json

import azure.functions as func

from libs.home_assistant import get_usage_data
from libs.data import find_optimal_hop
from libs.pushover import send_pushover_notification
from libs.electrickiwi import ElectricKiwi

app = func.FunctionApp()


@app.function_name(name="HourOfPower")
@app.timer_trigger(schedule="0 55 23 * * *",
                   arg_name="mytimer",
                   run_on_startup=True)
def hour_of_power(mytimer: func.TimerRequest) -> None:
    try:
        usage_data = get_usage_data(
            url=os.environ["HOME_ASSISTANT_URL"],
            token=os.environ["HOME_ASSISTANT_ACCESS_TOKEN"],
            entity_id=os.environ["HOME_ASSISTANT_ENTITY_ID"]
        )

        # clean the data
        usage_data.pop(0)  # remove the first element as its just metadata
        usage_data = [obj for obj in usage_data if obj["state"]
                      != "unavailable"]  # remove any unavailable states

        start_time, end_time, total_kwh, cost = find_optimal_hop(usage_data)

        # Generate a list of all possible HOPs using list comprehension
        ek_hours = [
            '12:00 AM', '12:30 AM', '01:00 AM', '01:30 AM', '02:00 AM', '02:30 AM',
            '03:00 AM', '03:30 AM', '04:00 AM', '04:30 AM', '05:00 AM', '05:30 AM',
            '06:00 AM', '06:30 AM', '07:00 AM', '07:30 AM', '08:00 AM', '08:30 AM',
            '09:00 AM', '09:30 AM', '10:00 AM', '10:30 AM', '11:00 AM', '11:30 AM',
            '12:00 PM', '12:30 PM', '01:00 PM', '01:30 PM', '02:00 PM', '02:30 PM',
            '03:00 PM', '03:30 PM', '04:00 PM', '04:30 PM', '05:00 PM', '05:30 PM',
            '06:00 PM', '06:30 PM', '07:00 PM', '07:30 PM', '08:00 PM', '08:30 PM',
            '09:00 PM', '09:30 PM', '10:00 PM', '10:30 PM', '11:00 PM', '11:30 PM'
        ]

        ek = ElectricKiwi()
        token = ek.at_token()
        ek.login(
            email=os.environ["ELECTRIC_KIWI_EMAIL"],
            password_hash=ek.password_hash(
                os.environ["ELECTRIC_KIWI_PASSWORD"])
        )
        ek.set_hop_hour(ek_hours.index(start_time)+1)

    except Exception as e:
        logging.error(e)
        send_pushover_notification(
            user_key=os.environ["PUSHOVER_USER_KEY"],
            api_token=os.environ["PUSHOVER_API_TOKEN"],
            message=f"An error occurred: {e}",
            title="Hour of Power Optimiser - Error"
        )

    else:
        send_pushover_notification(
            user_key=os.environ["PUSHOVER_USER_KEY"],
            api_token=os.environ["PUSHOVER_API_TOKEN"],
            message=f"Hour of Power: {start_time} - {end_time}\nTotal kWh: {total_kwh} kWh\nEstimated Savings: ${cost}",
            title="Hour of Power Optimiser"
        )
