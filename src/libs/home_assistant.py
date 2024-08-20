import requests
import logging
import json
import os


def get_usage_data(url, token, entity_id):
    """
    This function gets the kWh usage from Home Assistant
    """
    headers = {
        "Authorization": "Bearer " + token,
        "content-type": "application/json",
    }
    parameters = {
        "filter_entity_id": entity_id,
        "minimal_response": ""
    }

    # The <timestamp> (YYYY-MM-DDThh:mm:ssTZD) is optional and defaults to 1 day before the time of the request.
    # It determines the beginning of the period.
    api_url = url + "/api/history/period"
    response = requests.get(api_url, params=parameters, headers=headers)
    response.raise_for_status()

    if response.status_code != 200:
        logging.error(f"Error getting usage data: {response.text}")
        return None

    usage_data = json.loads(response.text)
    usage_data = usage_data[0]

    usage_data_entries = len(usage_data)
    logging.info(
        f"Retrieved {usage_data_entries} usage entries from Home Assistant")

    if os.getenv("AZURE_FUNCTIONS_ENVIRONMENT") == 'Development':
        with open('usage_data.json', 'w', encoding='utf-8') as f:
            json.dump(usage_data, f, indent=4)

    return usage_data
