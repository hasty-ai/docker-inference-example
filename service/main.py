import argparse
import logging
import os
import sys

import waitress
import flask
from flask import Flask

from service.endpoints.inference import inference_api
from service.serving.registry import models_registry

C_MODEL_FOLDER = "model"

# Set up logger
log_format = "%(levelname)s %(asctime)s %(request_id)s - %(message)s"
LOGLEVEL = os.environ.get('LOGLEVEL', 'INFO').upper()
logging.basicConfig(stream=sys.stdout,
                    format=log_format,
                    level=LOGLEVEL)
old_factory = logging.getLogRecordFactory()


def record_factory(* args, ** kwargs):
    record = old_factory(* args, ** kwargs)
    try:
        record.request_id = flask.g.request_id
    except Exception as e:
        record.request_id = ''
    return record


logging.setLogRecordFactory(record_factory)
logging.info(f"Using log level {LOGLEVEL}")

# Flask app with database configuration.
app = Flask('Inference Service')
app.register_blueprint(inference_api)

if __name__ == '__main__':
    for model_name in os.listdir(C_MODEL_FOLDER):
        model_path = os.path.join(C_MODEL_FOLDER, model_name)
        if os.path.isdir(model_path):
            model_family = models_registry.get_model_family(model_path)
            if model_family:
                models_registry.load_model(model_family, model_path, model_name)
    waitress.serve(app, host='0.0.0.0', port='5000', threads=8)
