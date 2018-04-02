# encoding: utf-8
import socket
import select
import logging
import random


from connection import Connection, DIR_READ, DIR_WRITE, RequestHandlerTask


class Proxy(object):
    """Proxy HTTP"""

    def __init__(self, port, hosts):
        """
        Inicializar, escuchando en port, y sirviendo los hosts indicados en
        el mapa `hosts`
        """

        # Conexión maestra (entrante)
        master_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        master_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        master_socket.bind(('', port))
        logging.info("Listening on %d", port)
        master_socket.listen(5)
        self.host_map = hosts
        self.connections = []
        self.master_socket = master_socket
        # AGREGAR estado si lo necesitan

    def run(self):
        """Manejar datos de conexiones hasta que todas se cierren"""
        while True:
            self.handle_ready()
            p = self.polling_set()
            events = p.poll()
            self.handle_events(events)
            self.remove_finished()

    def polling_set(self):
        """
        Devuelve objeto polleable, con los eventos que corresponden a cada
        una de las conexiones.
        Si alguna conexión tiene procesamiento pendiente (que no requiera
        I/O), realiza ese procesamiento antes de poner la conexión en el
        conjunto.
        """
        p = select.poll()
        p.register(self.master_socket.fileno(), select.POLLIN)
        for conn in self.connections:
            if conn.direction() == DIR_READ:
                p.register(conn.fileno(), select.POLLIN)
            elif conn.direction() == DIR_WRITE:
                p.register(conn.fileno(), select.POLLOUT)
        # COMPLETAR. Llamadas a register que correspondan, con los eventos
        # que correspondan
        return p

    def connection_with_fd(self, fd):
        """
        Devuelve la conexión con el descriptor fd
        """
        for conn in self.connections:
            if conn.fileno() == fd:
                return conn

    def handle_ready(self):
        """
        Hace procesamiento en las conexiones que tienen trabajo por hacer.
        Es decir, las que estan leyendo y tienen datos en la cola de entrada
        """
        for c in self.connections:
            # Hacer avanzar la maquinita de estados
            if c.input.data:
                c.task = c.task.apply(c)

    def handle_events(self, events):
        """
        Maneja eventos en las conexiones. events es una
        lista de pares (fd, evento)
        """
        for (fd, event) in events:
            if self.master_socket.fileno() == fd:
                self.accept_new()
            else:
                if event & select.POLLOUT:
                    self.connection_with_fd(fd).send()
                elif event & select.POLLIN:
                    self.connection_with_fd(fd).recv()

    def accept_new(self):
        """Acepta una nueva conexión"""
        new_conn, ip = self.master_socket.accept()
        new_client = Connection(new_conn, ip)
        new_client.task = RequestHandlerTask(self)
        self.append(new_client)

    def remove_finished(self):
        """
        Elimina conexiones marcadas para terminar
        """
        for conn in self.connections:
            if conn.remove:
                conn.close()
                self.connections.remove(conn)

    def connect(self, hostname):
        """
        Establece una nueva conexion saliente al hostname dado. El
        hostname puede tener la forma host:puerto ; si se omite el
        :puerto se asume puerto 80.

        Aqui esta la unica llamada a connect() del sistema. No
        preocuparse por el caso de connect() bloqueante
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if ':' in hostname:
            parts = hostname.split(':')
            host = parts[0]
            puerto = parts[1]
        else:
            host = hostname
            puerto = 80
        s.connect((host, puerto))
        return s

    def append(self, c):
        self.connections.append(c)

    def connect_to_random_ip(self, host):
        host = host[1: ]
        all_ips = self.host_map[host]
        ip = random.choice(all_ips)
        s = self.connect(ip)
        conn = Connection(s, ip)
        self.append(conn)
        return conn
