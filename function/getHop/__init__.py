import datetime
import logging
import os
from decimal import Decimal

import arrow
import azure.functions as func

from ElectricKiwi.electrickiwi import ElectricKiwi, hop_score

def main(mytimer: func.TimerRequest) -> None:
    utc_timestamp = datetime.datetime.utcnow().replace(
        tzinfo=datetime.timezone.utc).isoformat()

    # if mytimer.past_due:
    logging.info('The timer is past due!')

    # Get environment variables
    ek_email = os.environ["EK_EMAIL"]
    ek_password = os.environ["EK_PASSWORD"]

    ek = ElectricKiwi()
    token = ek.at_token()

    customer = ek.login(ek_email, ek.password_hash(ek_password))
    print('Logged in: OK')

    connection  = ek.connection_details()

    kwh_cost    = Decimal(connection['pricing_plan']['usage_rate_inc_gst'])
    wrong_kwh   = Decimal('0.0')
    hop_savings = Decimal('0.0')

    print("")
    consumption = ek.consumption(arrow.now().shift(days=-2), arrow.now())
    for date in consumption:
        data = consumption[date]

        hop_usage = Decimal(data['consumption_adjustment'])
        hop_savings += hop_usage
        hop_best_hour = []

        for interval in range(1, 24*2):
            interval_data = data['intervals'][str(interval)]
            if interval_data['hop_best']:
                hop_best = Decimal(interval_data['consumption']) + Decimal(data['intervals'][str(interval+1)]['consumption'])
                hop_best_hour.append(interval_data['time'])
                break

        date = arrow.get(date, 'YYYY-MM-DD').format('DD/MM/YYYY')

        diff = hop_best - hop_usage
        if diff > 0.01:
            wrong_kwh += diff
            logging.info('{} - Wrong HOP: {}kWh ({}) vs {}kWh ({}kWh)'.format(date, hop_best, hop_best_hour, hop_usage, diff))
        else:
            logging.info('{} - Correct HOP: {}kWh'.format(date, hop_usage))

    logging.info('\nHOP Savings: {}kWh (${:.2f})'.format(hop_savings, hop_savings * kwh_cost))
    logging.info('Missed HOP: {}kWh (${:.2f})'.format(wrong_kwh, wrong_kwh * kwh_cost))
    logging.info('HOP Score: {:.2f}%'.format(Decimal(100.0) - ((wrong_kwh / hop_savings) * 100)))

    logging.info('Python timer trigger function ran at %s', utc_timestamp)