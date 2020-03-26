from flask import Flask, jsonify, request, render_template
import os, sys
import json
import pprint
import codecs
import wand
from wand.image import Image
from wand.color import Color
from werkzeug.utils import secure_filename
from datetime import datetime
import chardet
from pdfminer3.pdfparser import PDFParser
from pdfminer3.pdfdocument import PDFDocument
from pdfminer3.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer3.converter import TextConverter
from pdfminer3.layout import LAParams
from pdfminer3.pdfpage import PDFPage
from pdfminer3.pdftypes import resolve1, PDFObjRef
from io import StringIO, TextIOWrapper, BytesIO
import csv
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



class Document():
    """
    curl -F file=@./totti.txt http://0.0.0.0:24222/json
    """
    doc_name = ''
    output_path = ""
    extension = ''
    file = b''
    properties = {}
    content = []
    
    def __init__(self, file, doc_name):
        self.doc_name = doc_name
        self.extension = self.get_extension()
        self.content = []
        self.output_path = "output_dir/" 
        self.file = file
        self.properties = {}
        
    def writeToLocal(self):
        path = os.path.join(os.path.join(os.getcwd(), self.output_path), self.doc_name)
        opt = ''
        if self.extension in ['csv', 'pdf']:
            opt='wb'
        elif self.extension in ['txt']:
            opt='w'
        else:
            try:
                opt = self.extension
                with open(path, opt) as fo:
                    fo.write(self.content)
            except :
                print("Erreur extension non supporté pour l'écriture du fichier en local")
                pass;
        with open(path, opt) as fo:
            fo.write(self.content)
        return path
        
    def extract_textFile(self):
        assert self.extension in ['txt']

        self.content = " ".join([x.decode("utf-8") for x in self.file.readlines()])         
        self.properties['content'] = self.content
        
        f_path = self.writeToLocal()
        #print(os.listdir(os.getcwd()))
        with open(f_path, 'rb') as f:
            raw_data = f.read()
            self.properties['size'] = f.tell()
            self.properties['encoding'] = chardet.detect(raw_data)
            self.properties['word_count'] = len(self.content.split(' '))        
        return self.properties
    
    def get_extension(self):
        self.extension = self.doc_name.split('/')[-1].split('.')[-1].lower()
        return self.extension
    
    def refersTo(self):
        if self.extension in ['png', 'jpeg', 'jpg', 'jfif']:
            return self.extract_images()
        elif self.extension == 'pdf':
            return self.extract_pdf()
        elif self.extension == 'txt':
            return self.extract_textFile()
        elif self.extension in ['csv', 'xlsx']:
            return self.extract_csv()
        else:
            err = {"error": 'Unsupported extension: ".{}"'.format(self.extension)}
            return err
        
    def extract_images(self):
        self.properties = {}
        assert self.extension in ['jpeg', 'jpg', 'png', 'jfif']
        #self.file = self.file.read()
        with Image(blob= self.file, format='ico') as i:
            dim = {"width": i.width, "height": i.height}
            self.properties["dimensions"] = dim
            self.properties["alpha_channel"] = i.alpha_channel
            self.properties["format"] = i.format
            self.properties["type_image"] = i.type 
            self.properties["compression_quality"] = i.compression_quality
            self.properties["compression"] = i.compression
            i.save(filename = os.path.join(os.path.join(os.getcwd(), self.output_path), self.doc_name))

            return self.properties
        
    def convert_pdf_to_txt(self):
        rsrcmgr = PDFResourceManager()
        retstr = StringIO()
        codec = 'utf-8'
        laparams = LAParams()
        device = TextConverter(rsrcmgr, retstr, laparams=laparams)
        
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        password = ""
        maxpages = 0
        caching = True
        pagenos=set()

        for page in PDFPage.get_pages(self.file, pagenos, maxpages=maxpages, password=password,caching=caching, check_extractable=True):
            interpreter.process_page(page)

        text = retstr.getvalue()

        device.close()
        retstr.close()
        return text

    def convertPdfDatetime(self, pdf_date):
        dtformat = "%Y%m%d%H%M%S"
        if b'+' in pdf_date:
            clean = pdf_date.decode("utf-8").replace("D:","").split('+')[0]
        elif b'-' in pdf_date:
            clean = pdf_date.decode("utf-8").replace("D:","").split('-')[0]
        else:
            clean = pdf_date.decode("utf-8").replace("D:","")[:-7]
        return datetime.strptime(clean, dtformat)
    
    
    def extract_pdf(self):
        assert self.extension in ['pdf']
        
        self.content = self.file.read()
        parser = PDFParser(self.file)
        doc = PDFDocument(parser)
        
        available_fields = list(doc.info[0].keys())
        self.properties['auteur'] = None
        self.properties['creation_date'] = None
        self.properties['modification_date'] = None
        self.properties['creator'] = None
        self.properties['producer'] = None
        
        if 'CreationDate' in available_fields:
            if isinstance(doc.info[0]["CreationDate"], PDFObjRef):
                doc.info[0]["CreationDate"] = resolve1(doc.info[0]["CreationDate"])
            try:        
                pdf_creation_date = str(self.convertPdfDatetime(doc.info[0]["CreationDate"]))
                self.properties['creation_date'] = str(pdf_creation_date)
            except:
                pass;
        if 'ModDate' in available_fields:
            if isinstance(doc.info[0]["ModDate"], PDFObjRef):
                doc.info[0]["ModDate"] = resolve1(doc.info[0]["ModDate"])
                    
            try:
                pdf_modif_date =  str(self.convertPdfDatetime(doc.info[0]["ModDate"]))
                self.properties['modification_date'] = str(pdf_modif_date)
            except:
                pass;
        if 'Author' in available_fields:
            if isinstance(doc.info[0]["Author"], PDFObjRef):
                doc.info[0]["Author"] = resolve1(doc.info[0]["Author"])
            try:        
                pdf_auteur = doc.info[0]["Author"].decode("utf-8")
                self.properties['auteur'] = pdf_auteur
            except:
                pass;
        if 'Creator' in available_fields:
            if isinstance(doc.info[0]["Creator"], PDFObjRef):
                doc.info[0]["Creator"] = resolve1(doc.info[0]["Creator"])
            try:    
                pdf_creator = doc.info[0]["Creator"].decode("utf-16")
                self.properties['creator'] = pdf_creator
            except:
                pass;
        if 'Producer' in available_fields:
            if isinstance(doc.info[0]["Producer"], PDFObjRef):
                doc.info[0]["Producer"] = resolve1(doc.info[0]["Producer"])
            try:    
                pdf_producer = doc.info[0]["Producer"].decode("utf-16")
                self.properties['producer'] = pdf_producer
            except:
                pass;
            
        parser.set_document(doc)
        pages = resolve1(doc.catalog['Pages'])
        pages_count = pages.get('Count', 0)
        
        #Only the first 300 characters for clarity
        self.content = self.convert_pdf_to_txt()
        self.properties['content'] = self.content[:300] + '(...)'
        self.properties['page_count'] = pages_count

        return self.properties

    
    def extract_csv(self):
        assert self.extension in ['csv']
        
        self.content = self.file.read()
        
        f_path = self.writeToLocal()
        self.properties['filename'] = self.doc_name.split('/')[-1]
        self.properties['extension'] = self.get_extension()
        
        file_size = os.stat(f_path).st_size
        self.properties["size"] = file_size
        wrapper = TextIOWrapper(codecs.getreader("utf-8")(self.file))
        wrapper.seek(0,0)
        
        reader = csv.DictReader(wrapper)
        
        data_columns = []
        file_delimiter = ''
        
        for row in reader:
            items = {k: v for k, v in row.items()}
            for key in items.keys():
                if ';' in key:
                    file_delimiter = ';'
                else:
                    file_delimiter = ','
                data_columns = [x for x in list(items.keys())]
                if file_delimiter == ';':
                    data_columns = data_columns[0].split(';')
                break;
            break;
            
        row_count = sum(1 for row in reader)

        self.properties['content'] = self.content.decode('utf-8')[:300]
        self.properties["nb_rows"] = row_count
        self.properties["file_delimiter"] = file_delimiter
        self.properties["header_columns"] = data_columns
        return self.properties
                
    
    def build_heads():
        print('next time')

@app.route('/', methods=["GET"])
def index():
    return("Hello SIO")

@swag_from('upload_json.yml')
@app.route('/json', methods=["POST"])
def upload():
    dico = {}
    dico['metadata'] = {}
    output_dir = os.path.join(os.getcwd(),'output_dir/')
    if request.method == 'POST':
        file = request.files['file']
        f_name = request.files["file"].filename
        #print(file.read())
        #print(type(file))
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
            #resp = json.dumps(file_content['error'], ensure_ascii=False) 
            resp = jsonify({'message' : _data['error']})
            resp.status_code = 400
            return resp
        try:
            with open(os.path.join(output_dir, f_name.split('.')[0]) + '.json', 'w+') as outfile:
                    json.dump(dico, outfile)
        except:
            print("Can't write json")
        
        return jsonify(dico)
        #return json.dumps(dico, ensure_ascii=False).encode('utf8')
    else:
        resp = jsonify({'message' : 'Cette méthode ne peut être exécuté que par un POST'})
        resp.status_code = 405
        return resp

@swag_from('get_json.yml')
@app.route('/get_json/<name_ID>', methods=["GET"])
def read_json(name_ID):
    output_dir = os.path.join(os.getcwd(),'output_dir/')
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
    app.run(debug=True, port=24222, host="0.0.0.0")    
