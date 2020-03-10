from flask import Flask, jsonify, request, render_template
import os
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
from pdfminer3.pdftypes import resolve1
from io import StringIO
import csv

app = Flask(__name__)

class Document():
    """
    curl -X post file=@./rest.txt http://127.0.0.1:5000/json
    """
    endpoint = ''
    extension = ''
    file = b''
    metadata = {}
    content = []
    
    def __init__(self, file, endpoint):
        self.endpoint = endpoint
        self.extension = self.get_extension()
        self.content = []
        self.file = file
        self.metadata = {}
        
    def writeToLocal(self):
        path = os.path.join(os.getcwd(), self.endpoint)
        opt = ''
        if self.extension in ['csv', 'pdf']:
            opt='wb'
        elif self.extension in ['txt']:
            opt='w'
        else:
            opt='ragnagna'
        with open(path,opt) as fo:
            fo.write(self.content)
        return path
        
    def extract_textFile(self):
        assert self.extension in ['txt']

        self.content = " ".join([x.decode("utf-8") for x in self.file.readlines()])         
        self.metadata['content'] = self.content
        
        f_path = self.writeToLocal()
        #print(os.listdir(os.getcwd()))
        
        with open(f_path, 'rb') as f:
            raw_data = f.read()
            self.metadata['size'] = f.tell()
            self.metadata['encoding'] = chardet.detect(raw_data)
        return self.metadata
    
    def get_extension(self):
        self.extension = self.endpoint.split('/')[-1].split('.')[-1].lower()
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
        
    def extract_images(self):
        self.metadata = {}
        assert self.extension in ['jpeg', 'jpg', 'png', 'jfif']
        self.file = self.file.read()
        with Image(blob = self.file) as i:
            dim = {"width": i.width, "height": i.height}
            self.metadata["dimensions"] = dim
            self.metadata["alpha_channel"] = i.alpha_channel
            self.metadata["format"] = i.format
            self.metadata["type_image"] = i.type 
            #self.metadata["background_color"] = i.background_color 
            self.metadata["compression_quality"] = i.compression_quality
            self.metadata["compression"] = i.compression
            return self.metadata
        
    def convert_pdf_to_txt(self, f_path):
        rsrcmgr = PDFResourceManager()
        retstr = StringIO()
        codec = 'utf-8'
        laparams = LAParams()
        device = TextConverter(rsrcmgr, retstr, laparams=laparams)
        
        fp = open(f_path, 'rb')
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        password = ""
        maxpages = 0
        caching = True
        pagenos=set()

        for page in PDFPage.get_pages(fp, pagenos, maxpages=maxpages, password=password,caching=caching, check_extractable=True):
            interpreter.process_page(page)

        text = retstr.getvalue()

        fp.close()
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
        f_path = self.writeToLocal()
        fp =open(f_path, 'rb')
        
        parser = PDFParser(fp)
        doc = PDFDocument(parser)
        
        available_fields = list(doc.info[0].keys())
        #print(available_fields)

        if 'CreationDate' in available_fields:
            try:
                pdf_creation_date = str(convertPdfDatetime(doc.info[0]["CreationDate"]))
                self.metadata['creation_date'] = str(pdf_creation_date)
            except:
                pass;
        if 'ModDate' in available_fields:
            try:
                pdf_modif_date =  convertPdfDatetime(doc.info[0]["ModDate"])
                self.metadata['modification_date'] = str(pdf_modif_date)
            except:
                pass;
        if 'Author' in available_fields:
            try:
                pdf_auteur = doc.info[0]["Author"].decode("utf-8")
                self.metadata['auteur'] = pdf_auteur
            except:
                pass;
        if 'Creator' in available_fields:
            try:
                pdf_creator = doc.info[0]["Creator"].decode("utf-8")
                self.metadata['creator'] = pdf_creator
            except:
                pass;
        if 'Producer' in available_fields:
            try:
                pdf_producer = doc.info[0]["Producer"].decode("utf-8")
                self.metadata['producer'] = pdf_producer
            except:
                pass;
            
        parser.set_document(doc)
        pages = resolve1(doc.catalog['Pages'])
        pages_count = pages.get('Count', 0)
        
        #Only the first 100 characters for clarity
        self.content = self.convert_pdf_to_txt(f_path)
        self.metadata['content'] = self.content[:100] + '(...)'
        self.metadata['page_count'] = pages_count

        return self.metadata

    
    def extract_csv(self):
        assert self.extension in ['csv']
        
        metadata = {}
        ##fileString = open(self.endpoint, 'r', newline = '')
        self.content = self.file.read()
        f_path = self.writeToLocal()
        fileString =open(f_path, 'r', newline='')
        
        metadata['filename'] = self.endpoint.split('/')[-1]
        metadata['extension'] = self.get_extension()
        
        file_size = os.stat(f_path).st_size
        metadata["size"] = file_size

        reader = csv.DictReader(fileString)
        data_columns = []
        file_delimiter = ''
        
        for row in reader:
            items = {k: v for k, v in row.items()}
            for key in items.keys():
                if ';' in key:
                    file_delimiter = ';'
                else:
                    file_delimiter = ','
                data_columns = [x for x in key.split(file_delimiter)]
                break;
            break;
            
        row_count = sum(1 for row in reader)
        metadata["nb_rows"] = row_count
        metadata["file_delimiter"] = file_delimiter
        metadata["header_columns"] = data_columns
        return metadata
                
    
    def build_heads():
        print('next time')

@app.route('/<var>', methods=["GET"])
def index(var):
    return "Hello {}".format(var)
    
@app.route('/json', methods=["POST"])
def upload():
    dico = {}
    if request.method == 'POST':
        file = request.files['file']
        #print(request.files["file"].content_type)
        f_name = request.files["file"].filename
        doc = Document(file, f_name)
        #aiguille l'extraction des métadonnées dépendant de l'extension du document
        meta = doc.refersTo() 
        dico['file_metadata'] = meta
        #print(dico['file_metadata'])

        return jsonify(dico)
        #return json.dumps(dico, ensure_ascii=False).encode('utf8')    
        
    
    
    
if __name__ == '__main__':
    app.run()    
