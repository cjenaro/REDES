#!/usr/bin/env python
# encoding: utf-8
# Revisión 2014 Carlos Bederián
# Revisión 2011 Nicolás Wolovick
# Copyright 2008-2010 Natalia Bidart y Daniel Moisset
# $Id: server.py 656 2013-03-18 23:49:11Z bc $

import optparse
import socket
import select
import connection
from constants import *


class AsyncServer(object):
    """
    El servidor, que crea y atiende el socket en la dirección y puerto
    especificados donde se reciben nuevas conexiones de clientes.
    """

    def __init__(self, addr=DEFAULT_ADDR, port=DEFAULT_PORT,
                 directory=DEFAULT_DIR):
        print "Serving %s on %s:%s." % (directory, addr, port)
        self.directory = directory
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((addr, port))
        self.server.listen(5)
        self.server.setblocking(0)

    def serve(self):
        """
        Loop principal del servidor. Se acepta una conexión a la vez
        y se espera a que concluya antes de seguir.
        """
        poll = select.poll()
        poll.register(self.server, select.POLLIN)
        clients = {}

        while True:
            events = poll.poll()
            for fileno, event in events:
                if fileno == self.server.fileno():
                    if event & select.POLLIN:
                        client_socket, client_address = self.server.accept()
                        client_socket.setblocking(0)
                        poll.register(client_socket.fileno(), select.POLLIN)
                        clients[client_socket.fileno()] =
                        connection.Connection(client_socket, self.directory)
                        print('New client: ' + str(client_address))
                else:
                    conn = clients[fileno]
                    if conn.remove:
                        if event & select.POLLOUT:
                            conn.handle_output()
                        poll.unregister(fileno)
                        del clients[fileno]
                        conn.socket.close()
                    if event & select.POLLIN:
                        conn.handle_input()
                        new_event = conn.events()
                        poll.register(fileno, new_event)
                    if event & select.POLLOUT:
                        conn.handle_output()
                        new_event = conn.events()
                        poll.register(fileno, new_event)


def main():
    """Parsea los argumentos y lanza el server"""

    parser = optparse.OptionParser()
    parser.add_option(
        "-p", "--port",
        help=u"Número de puerto TCP donde escuchar", default=DEFAULT_PORT)
    parser.add_option(
        "-a", "--address",
        help=u"Dirección donde escuchar", default=DEFAULT_ADDR)
    parser.add_option(
        "-d", "--datadir",
        help=u"Directorio compartido", default=DEFAULT_DIR)

    options, args = parser.parse_args()
    if len(args) > 0:
        parser.print_help()
        sys.exit(1)
    try:
        port = int(options.port)
    except ValueError:
        sys.stderr.write(
            "Numero de puerto invalido: %s\n" % repr(options.port))
        parser.print_help()
        sys.exit(1)

    server = AsyncServer(options.address, port, options.datadir)
    server.serve()

if __name__ == '__main__':
    main()
