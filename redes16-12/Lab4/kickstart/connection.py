# encoding: utf-8
# $Rev: 512 $

"""
Módulo que provee manejo de conexiones genéricas
"""

from socket import error as socket_error
import logging
from queue import Queue, ProtocolError, BAD_REQUEST, SEPARATOR

# Estados posibles de la conexion
DIR_READ = +1   # Hay que esperar que lleguen más datos
DIR_WRITE = -1  # Hay datos para enviar


class Connection(object):
    """Abstracción de conexión. Maneja colas de entrada y salida de datos,
    y una funcion de estado (task). Maneja tambien el avance de la maquina de
    estados.
    """

    def __init__(self, fd, address=''):
        """Crea una conexión asociada al descriptor fd"""
        self.socket = fd
        self.task = None  # El estado de la maquina de estados
        self.input = Queue()
        self.output = Queue()
        self.remove = False
        self.address = address

    def fileno(self):
        """
        Número de descriptor del socket asociado.
        Este metodo tiene que existir y llamarse así para poder pasar
        instancias de esta clase a select.poll()
        """
        return self.socket.fileno()

    def direction(self):
        """
        Modo de la conexión, devuelve uno de las constantes DIR_*; también
        puede devolver None si el estado es el final y no hay datos para
        enviar.
        """
        if self.output.data == '':
            return DIR_READ
        elif self.output.data != '':
            return DIR_WRITE
        elif self.task is None:
            return None
        # COMPLETAR

    def recv(self):
        """
        Lee datos del socket y los pone en la cola de entrada.
        También maneja lo que pasa cuando el remoto se desconecta.
        Aqui va la unica llamada a recv() sobre sockets.
        """

        self.input.put(self.socket.recv(4096))
        # COMPLETAR

    def send(self):
        """Manda lo que se pueda de la cola de salida"""

        self.socket.send(self.output.data)
        self.output.clear()
        # COMPLETAR

    def close(self):
        """Cierra el socket. OJO que tambien hay que avisarle al proxy que nos
        borre.
        """
        self.socket.close()
        self.remove = True
        self.output.clear()

    def send_error(self, code, message):
        """Funcion auxiliar para mandar un mensaje de error"""
        logging.warning("Generating error response %s [%s]", code, self.address)
        self.output.put("HTTP/1.1 %d %s\r\n" % (code, message))
        self.output.put("Content-Type: text/html\r\n")
        self.output.put("\r\n")
        self.output.put("<body><h1>%d ERROR: %s</h1></body>\r\n" % (code, message))
        self.remove = True


class Forward(object):
    """Estado: todo lo que venga, lo retransmito a la conexión target"""

    def __init__(self, target):
        self.target = target

    def apply(self, connection):
        if connection.input.data == '':
            self.target.remove = True
            return None
        else:
            self.target.output.put(connection.input.data)
            connection.input.clear()
            return self


class RequestHandlerTask(object):

    def __init__(self, proxy):
        self.proxy = proxy
        ### Agregar cosas si hace falta para llevar estado interno.
        # Puede que les convenga llevar
        self.host = None
        self.url = None

    def apply(self, connection):
        method, self.url, protocol = connection.input.read_request_line()
        if method is None and self.url is None and protocol is None:
            connection.send_error(BAD_REQUEST, 'Bad request')
            return None
        else:
            try:
                if connection.input.parse_headers():
                    for header in connection.input.headers:
                        if header[0] == 'Host':
                            self.host = header[1]
                    auxconn = self.proxy.connect_to_random_ip(self.host)
                    auxconn.output.put(method + ' ' + self.url + ' ' +
                                       protocol + SEPARATOR)
                    for header in connection.input.headers:
                        if header[0] == 'Connection':
                            auxconn.output.put(header[0] + ': close' +
                                               SEPARATOR)
                        else:
                            auxconn.output.put(header[0] + ': ' + header[1] + SEPARATOR)
                    auxconn.output.put(SEPARATOR)
                    forward = Forward(auxconn)
                    auxforward = Forward(connection)
                    auxconn.task = auxforward
                    return forward
                else:
                    return self
            except:
                connection.send_error(403, 'Forbidden')
