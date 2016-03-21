#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import unittest, threading
from http.server import HTTPServer, SimpleHTTPRequestHandler

server = None


def start_server():
    global server
    server_address = ('', 8000)
    handler_class = SimpleHTTPRequestHandler
    server = HTTPServer(server_address, handler_class)
    t = threading.Thread(target=server.serve_forever)
    t.daemon = True
    print("Starting server at http://localhost:8000/")
    t.start()


def stop_server():
    global server
    print("Closing server at http://localhost:8000/")
    server.server_close()


start_server()
input("Press Enter to stop.\n>")
stop_server()






