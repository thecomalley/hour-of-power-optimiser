import datetime
import logging

import azure.functions as func

from HourOfPower.power_savings import get_days_usage, find_peak_hop, set_hop, notify_hass

def main(mytimer: func.TimerRequest) -> None:
    
    utc_timestamp = datetime.datetime.utcnow().replace(
        tzinfo=datetime.timezone.utc).isoformat()
    
    try:
        logging.info('Function Starting!') 
    
        usage = get_days_usage()
        
        peak_kwh, peak_hop = find_peak_hop(usage)
        logging.info(f"Peak kWh = {peak_kwh}")
        logging.info(f"Peak Hour = {peak_hop}")
        
        hop = set_hop(peak_hop)
        logging.info(f"HoP successfully set to set to: {hop}")

        attributes = {
            "peak_kWh": peak_kwh
        }

        notify_hass(peak_hop,attributes)

    except:
        logging.exception('exception occurred!') 

    logging.info('Python timer trigger function ran at %s', utc_timestamp)