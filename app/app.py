import argparse
import os
from flask import Flask, jsonify, request, render_template, make_response, send_from_directory
import numpy as np
from datetime import datetime, date
import pprint
import json
from flask_cors import CORS
from flask_swagger_ui import get_swaggerui_blueprint
from routes import request_api


app = Flask(__name__)
CORS(app)

@app.route('/static/<path:path>', methods=["GET"])
def send_static(path):
    return send_from_directory('static', path)

### swagger specific ###
SWAGGER_URL = '/swagger'
API_URL = '/static/swagger.json'
SWAGGERUI_BLUEPRINT = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "filRouge-Etienne"
    }
)
app.register_blueprint(SWAGGERUI_BLUEPRINT, url_prefix=SWAGGER_URL)
### end swagger specific ###


app.register_blueprint(request_api.get_blueprint())


class Document():
    """
    curl -X POST -F file=@./rest.txt http://127.0.0.1:5000/json
    """
    endpoint = ''
    extension = ''
    text = ""
    taille = 0

    def __init__(self, endpoint):
        self.endpoint = endpoint

    def open(self):
        with open(self.endpoint) as f:
            for line in f:
                text.append(line) #ou json.loads(line)


    def get_ext(self):
        filename, file_extension = os.path.splitext(self.endpoint)
        return file_extension

    def build_heads():
        print('next time')

@app.route('/json', methods=["POST"])
def upload():
    #print(os.getcwd())
    dico = {}
    if request.method == 'POST':
        file = request.files['file'].read()
        file = file.decode("utf-8")
        dico['data'] = pprint.pformat(file)
        dico['meta'] = {"date": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3] }
        return jsonify(dico)
        #return json.dumps(dico, ensure_ascii=False).encode('utf8')


@app.route('/', methods=["GET"])
def index():
    return "<h1>Welcome to our server !!</h1>"

#curl -X GET http://127.0.0.1:5000/


if __name__ == '__main__':
    app.run(port='5000')
