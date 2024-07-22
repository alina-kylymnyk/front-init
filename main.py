from http.server import HTTPServer, BaseHTTPRequestHandler
import logging
import socket
import json
from pathlib import Path
import urllib.parse
import mimetypes
from jinja2 import Environment, FileSystemLoader
from threading import Thread

from jinja2 import Environment, FileSystemLoader

jinja = Environment(loader=FileSystemLoader('templates'))
BASE_DIR = Path()
BUFFER_SIZE = 1024
HTTP_PORT = 8080
HTTP_HOST = 'localhost'
SOCKET_HOST = '0.0.0.0'
SOCKET_PORT = 4000

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class GoitFramework(BaseHTTPRequestHandler):

    def do_GET(self):
        route = urllib.parse.urlparse(self.path)
        match route.path:
            case '/':
                self.send_html('index.html')
            case '/message':
                self.render_template('message.html')
            case _:
                file = BASE_DIR.joinpath(route.path[1:])
                if file.exists():
                    self.send_static(file)
                else:
                    # Перевірка наявності файлу в папці templates
                    template_file = Path('templates').joinpath(route.path[1:])
                    if template_file.exists():
                        self.send_static(template_file)
                    else:
                        self.send_html('error.html', 404)

    def do_POST(self):
        size = self.headers.get('Content-Length')
        data = self.rfile.read(int(size))
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.sendto(data,(SOCKET_HOST, SOCKET_PORT))
        client_socket.close()
        self.send_response(302)
        self.send_header('Location', '/message')
        self.end_headers()

    def send_html(self, filename, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as file:
            self.wfile.write(file.read())

    def render_template(self, filename, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        template = jinja.get_template(filename)
        content = template.render() 
        self.wfile.write(content.encode('utf-8'))

    def send_static(self, filename, status_code=200):
        self.send_response(status_code)
        mime_type, *_ = mimetypes.guess_type(filename)
        if mime_type:
            self.send_header('Content-Type', mime_type)
        else:
            self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        with open(filename, 'rb') as file:
            self.wfile.write(file.read())


def save_data_from_form(data):
    parse_data = urllib.parse.unquote_plus(data.decode())
    
    try:
        parse_dict = {key: value for key, value in [el.split('=')for el in parse_data.split('&')]}
        with open('storage/data.json', 'w', encoding='utf-8') as file:
            json.dump(parse_dict, file, ensure_ascii=False, indent=4)
    except ValueError as err:
        logging.error(err)
    except OSError as err:
        logging.error(err)


def run_socket_server(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((host, port))
    logging.info("Starting socket server")
    try:
       while True:
            msg, address = server_socket.recvfrom(BUFFER_SIZE)
            logging.info(f"Socket received {address}: {msg}")
            save_data_from_form(msg)
    except KeyboardInterrupt:
        pass
    finally:
        server_socket.close()

def run_http_server(host, port):
    address = (host, port)
    http_server = HTTPServer(address, GoitFramework)
    logging.info("HTTP Server is started")
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        http_server.server_close()



if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(ThreadName)s %(message)s')

server = Thread(target=run_http_server, args=(HTTP_HOST, HTTP_PORT))
server.start()

server_socket = Thread(target=run_socket_server, args=(SOCKET_HOST, SOCKET_PORT))
server_socket.start()