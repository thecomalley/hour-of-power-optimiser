import logging
import os
import json

import azure.functions as func

from libs import my_second_helper_function
from libs.home_assistant import get_usage_data
from libs.data import find_optimal_hop
from libs.pushover import send_pushover_notification

app = func.FunctionApp()

@app.function_name(name="HttpTrigger1")
@app.route(route="hello")
def test_function(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    usage_data = get_usage_data(
        url=os.environ["HOME_ASSISTANT_URL"], 
        token=os.environ["HOME_ASSISTANT_ACCESS_TOKEN"], 
        entity_id=os.environ["HOME_ASSISTANT_ENTITY_ID"]
    )

    # clean the data
    usage_data.pop(0) # remove the first element as its just metadata
    usage_data = [obj for obj in usage_data if obj["state"] != "unavailable"] # remove any unavailable states

    kwh, start_time, end_time = find_optimal_hop(usage_data)
    message = f"{kwh} kWh used between {start_time} and {end_time}"
    logging.info(message)

    send_pushover_notification(
        user_key=os.environ["PUSHOVER_USER_KEY"],
        api_token=os.environ["PUSHOVER_API_TOKEN"],
        message=message,
        title="Hour of Power Usage"
    )


    return func.HttpResponse(status_code=200, body="Hello World")
