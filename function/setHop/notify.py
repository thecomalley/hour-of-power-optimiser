# Function to notify the user via Pushover

import os
import logging
import requests
import json


def notify_pushover(message):
    logging.info('Sending notification to Pushover')

    try:
        url = "https://api.pushover.net/1/messages.json"

        data = {
            "token": os.environ['PUSHOVER_TOKEN'],
            "user": os.environ['PUSHOVER_USER'],
            "message": message,
            "priority": 0
        }

        r = requests.post(url, data=data)

        if r.status_code != 200:
            logging.error(r.text)

    except Exception as e:
        logging.error(e)
        raise e
