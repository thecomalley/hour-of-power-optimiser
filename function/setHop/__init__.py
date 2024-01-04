import datetime
from email import message
import logging

import azure.functions as func

from setHop.power_savings import get_days_usage, find_peak_hop, set_hop, notify_hass, get_last_days_usage, find_optimal_hop
from setHop.discord import notify_discord
from setHop.notify import notify_pushover


def main(mytimer: func.TimerRequest) -> None:
    today = datetime.date.today()
    logging.info(today.strftime(
        'Calculating optimal Hour of Power for: %d, %b %Y'))

    try:
        usage = get_days_usage()

        total_kwh, start_time, cost = find_optimal_hop(usage)

        set_hop(start_time)

        notify_pushover(
            f'Hour of Power set to {start_time} ({total_kwh:.2f} kWh), Estimated savings: ${cost:.2f}')

    except Exception as e:
        logging.error(e)
        raise e
