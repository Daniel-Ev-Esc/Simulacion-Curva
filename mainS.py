from http.server import BaseHTTPRequestHandler, HTTPServer
import logging
import json

import numpy as np
import modeloCarro

parameters2D = {
    'size': 40,
    'steps': 1000,
    'ndim': 2,
    'numAg' : 10 # Max 40
}

modelo = modeloCarro.CarModel(parameters=parameters2D)

modelo.setup()

def updateDatos():
    global modelo
    datos = modelo.update()
    modelo.step()
    return datos

def datosToJSON(ids,secciones,movimiento,rutaNum,semaforo):
    DICT = []
    for id in ids:
        dicc = {
            "id" : id,
            "seccion" : secciones[id],
            "movimiento" : movimiento[id],
            "numeroRuta": rutaNum[id],
            "Luz": semaforo[0][1],
            "Ruta": semaforo[0][0]
        }
        DICT.append(dicc)
    return json.dumps(DICT)

class Server(BaseHTTPRequestHandler):
    
    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
    def do_GET(self):
        logging.info("GET request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers))
        self._set_response()
        self.wfile.write("GET request for {}".format(self.path).encode('utf-8'))

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        #post_data = self.rfile.read(content_length)
        post_data = json.loads(self.rfile.read(content_length))
        #logging.info("POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n",
                     #str(self.path), str(self.headers), post_data.decode('utf-8'))
        logging.info("POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n")
        
        '''
        x = post_data['x'] * 2
        y = post_data['y'] * 2
        z = post_data['z'] * 2
        
        position = {
            "x" : x,
            "y" : y,
            "z" : z

            vector3(x,y,z)

            id : 0
            seccion : 1
            movimiento : 1

            objeto(id,seccion,movimiento)
        }

        self._set_response()
        #self.wfile.write("POST request for {}".format(self.path).encode('utf-8'))
        self.wfile.write(str(position).encode('utf-8'))
        '''
        
        datos = updateDatos()
        print(datos)
        self._set_response()
        resp = "{\"data\":" + datosToJSON(datos[0],datos[1],datos[2],datos[3],datos[4]) + "}"
        print(resp)
        self.wfile.write(resp.encode('utf-8'))

def run(server_class=HTTPServer, handler_class=Server, port=8585):
    logging.basicConfig(level=logging.INFO)
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    logging.info("Starting httpd...\n") # HTTPD is HTTP Daemon!
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:   # CTRL+C stops the server
        pass
    httpd.server_close()
    logging.info("Stopping httpd...\n")

if __name__ == '__main__':
    from sys import argv
    
    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()
