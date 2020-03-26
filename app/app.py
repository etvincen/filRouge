from model.document import Document
from flask import Flask, jsonify, request, render_template
import os, sys
import json
from werkzeug.utils import secure_filename
from datetime import datetime
from flasgger import Swagger, swag_from
from flasgger import LazyString, LazyJSONEncoder


app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.config["SWAGGER"] = {"title": "Swagger Fil Rouge","version":"0.1.0", "uiversion": 3, "description": "Interface pour les requêtes à l'API"}

swagger_config = {
    "headers": [
    ],
    "specs": [
        {
            "endpoint": 'apispec_1',
            "route": '/apispec_1.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/swaggerUI/"
}

template = dict(
    swaggerUiPrefix=LazyString(lambda: request.environ.get("HTTP_X_SCRIPT_NAME", ""))
)

app.json_encoder = LazyJSONEncoder

swagger = Swagger(app, config=swagger_config)

@app.route('/', methods=["GET"])
def index():
    return("Hello SIO")

@swag_from('upload_json.yml')
@app.route('/json', methods=["POST"])
def upload():
    dico = {}
    dico['metadata'] = {}
    output_dir = os.path.join(os.path.join(os.getcwd(),'app'),'output_dir/')
    if request.method == 'POST':
        file = request.files['file']
        f_name = request.files["file"].filename
        doc = Document(file, f_name)
        #aiguille l'extraction des métadonnées dépendant de l'extension du document
        _data = doc.refersTo() 
        if 'error' not in list(_data.keys()):
            content = ""
            for key, value in _data.items():
                if key != "content":
                    dico['metadata'][key] = value
                else:
                    dico[key] = value
            dico['metadata']['mime_type'] = request.files["file"].content_type
        else:
            resp = jsonify({'message' : _data['error']})
            resp.status_code = 400
            return resp
        try:
            with open(os.path.join(output_dir, f_name.split('.')[0]) + '.json', 'w+') as outfile:
                    json.dump(dico, outfile)
        except:
            print("Can't write json")
        
        return jsonify(dico)
    else:
        resp = jsonify({'message' : 'Cette méthode ne peut être exécuté que par un POST'})
        resp.status_code = 405
        return resp

@swag_from('get_json.yml')
@app.route('/get_json/<name_ID>', methods=["GET"])
def read_json(name_ID):
    output_dir = os.path.join(os.path.join(os.getcwd(),'app'),'output_dir/')
    json_dict = {}
    if name_ID.split('.')[-1] == 'json':
        try:
            with open(os.path.join(output_dir, name_ID), "r") as f:
                json_dict['data'] = json.load(f)
            resp = jsonify({'Contenu' : json_dict['data']})
            resp.status_code = 200
            return resp
        except:
            resp = jsonify({'message' : 'Le fichier json "{}" est introuvable'.format(name_ID)})
            resp.status_code = 404
    else:
        resp = jsonify({'message':'Vous devez passer un fichier json préalablement uploadé'})
        resp.status_code = 400

    return resp

    
    
if __name__ == '__main__':
    app.run(debug=False, port=24222, host="0.0.0.0")    
