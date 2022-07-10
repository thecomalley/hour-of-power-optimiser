import datetime
from email import message
import logging

import azure.functions as func

from setHop.power_savings import get_days_usage, find_peak_hop, set_hop, notify_hass, get_last_days_usage
from setHop.discord import notify_discord

def main(mytimer: func.TimerRequest) -> None:
    today = datetime.date.today()
    logging.info(today.strftime('Calculating optimal Hour of Power for: %d, %b %Y'))

    try:
        usage = get_days_usage()

        peak_kwh, peak_hop = find_peak_hop(usage)

        hop = set_hop(peak_hop)

        attributes = {
            "peak_kWh": peak_kwh
        }

        yesterday = get_last_days_usage()

        notify_hass(peak_hop,attributes)

        notify_discord(yesterday, peak_hop, peak_kwh)

    except Exception as e:
        logging.error(e)
        raise e
