# @Author      : 'Savvy'
# @Created_date: 2018/10/25 12:19 AM

from functools import partial
from http.server import BaseHTTPRequestHandler, HTTPServer
from database import Database
from sklearn import svm
from sklearn.externals import joblib
import json
import requests


# HTTPRequestHandler class
class myHTTPServer_RequestHandler(BaseHTTPRequestHandler):
    # pass the model to my http request handler
    def __init__(self, model, *args, **kwargs):
        self.model = model
        super().__init__(*args, **kwargs)
    
    # GET
    def do_GET(self):
        # Send response status code
        self.send_response(200)
        self.end_headers()

        # Get the size of data
        content_length = int(self.headers['Content-Length'])
        # Get the data itself
        get_data = self.rfile.read(content_length)
        print("GET request,\nBody:\n {}".format(get_data.decode('utf-8')))
        text = get_data.decode('utf-8')
        
        url='https://api.thingspeak.com/apps/thingtweet/1/statuses/update?api_key=TWBNG6JAE9GGEP13&status=%s'% text
        r = requests.post(url=url, json={}, headers={})
        print(r)
        return

    # PUT
    def do_PUT(self):
        global gestures
        # Send response status code
        self.send_response(200)
        self.end_headers()

        # Get the size of data
        content_length = int(self.headers['Content-Length'])
        # Get the data itself
        put_data = self.rfile.read(content_length)
        print("POST request,\nBody:\n {}".format(put_data.decode('utf-8')))
        data = json.loads(put_data.decode('utf-8'))
        traindata = {'label': 'A', 'data': data}
        Database.insert('Accelerometer1', traindata)
        print(traindata)
        return

    # POST
    def do_POST(self):
        # Send response status code
        self.send_response(200)
        self.end_headers()

        # Get the size of data
        content_length = int(self.headers['Content-Length'])
        # Get the data itself
        post_data = self.rfile.read(content_length)
        print("POST request,\nBody:\n {}".format(post_data.decode('utf-8')))
        data = json.loads(post_data.decode('utf-8'))
        result = self.model.predict([data])[0]
        self.wfile.write(result.encode('utf-8'))
        return


def run():
    print("Initialize database...")
    Database.initialize()
    print("Loading svc model...")
    clf = joblib.load('COLUMBIA_SVM_3.joblib')
    print("starting server...")
    # Server settings
    # Choose port 8080, for port 80, which is normally used for a http server, you need root access
    server_address = ('0.0.0.0', 80)
    handler = partial(myHTTPServer_RequestHandler, clf)
    httpd = HTTPServer(server_address, handler)
    print("running server...")
    httpd.serve_forever()


run()
