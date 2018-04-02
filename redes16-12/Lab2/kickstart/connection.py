# encoding: utf-8
# Copyright 2014 Carlos Bederián
# $Id: connection.py 455 2011-05-01 00:32:09Z carlos $

import socket
import string
import select
from constants import *
from os import listdir, stat
from os.path import isfile, join, getsize


class Connection(object):
    """
    Conexión punto a punto entre el servidor y un cliente.
    Se encarga de satisfacer los pedidos del cliente hasta
    que termina la conexión.
    """

    def __init__(self, socket, directory):
        self.socket = socket
        self.directory = directory
        self.connected = True
        self.buffer_input = ""
        self.buffer_output = ""
        self.remove = False

    def events(self):
        event = select.POLLOUT
        if (self.buffer_output == ""):
            event = select.POLLIN
        return (event)

    def handle_input(self):
        try:
            if EOL not in self.buffer_input:
                self.buffer_input = self.buffer_input + self.socket.recv(4096)
            else:
                request, self.buffer_input = self.buffer_input.split(EOL)
                if len(request) > 0 and "\n" not in request:
                    self.user_program(request)
                elif request == "":
                    self.socket_message(BAD_REQUEST)
                else:
                    self.socket_message(BAD_EOL)
        except socket.error:
            self.quit()

    def handle_output(self):
        try:
            self.socket.send(self.buffer_output)
            self.buffer_output = ""
        except socket.error():
            self.quit()

    def valid_filename(self, filename):
        valid_chars = '-_.%s%s' % (string.ascii_letters, string.digits)
        b = True
        for char in filename:
            if char not in valid_chars:
                b = False
        return b

    def get_file_listing(self):
        """
        Listado de archivos del directorio, ERROR 199 en caso de no tenerlos.
        """
        try:
            listd = listdir(self.directory)
        except:
            self.socket_message(INTERNAL_ERROR)
        else:
            self.socket_message(CODE_OK)
            for f in listd:
                if isfile(join(self.directory, f)):
                    self.buffer_output = self.buffer_output +
                    ("%s%s" % (f, EOL))
            self.buffer_output = self.buffer_output + (EOL)

    def get_metadata(self, request):
        """
        Devuelve el tamaño del archivo dado, ERROR 202 si no existe.
        """
        args = request.split(' ')
        if (len(args) == 2):
            filename = args[1]
            if self.valid_filename(filename):
                try:
                    filed = join(self.directory, filename)
                    size = str(getsize(filed))
                    self.socket_message(CODE_OK)
                    self.buffer_output = self.buffer_output +
                    ("%s %s" % (size, EOL))
                except OSError:
                    self.socket_message(FILE_NOT_FOUND)
                except ValueError:
                    self.socket_message(INVALID_ARGUMENTS)
                except:
                    self.socket_message(INTERNAL_ERROR)
            else:
                self.socket_message(INVALID_ARGUMENTS)
        else:
            self.socket_message(INVALID_ARGUMENTS)

    def get_slice(self, request):
        """
        Evalua argumentos, ERROR 201 si encuentra errores.
        """
        args = request.split(' ')
        if (len(args) == 4):
            filename = args[1]
            if self.valid_filename(filename):
                try:
                    size = int(args[2])
                    offset = int(args[3])

                    filed = join(self.directory, filename)
                    filesize = str(getsize(filed))
                    if ((offset + size) <= filesize):
                        fileopen = open(filed, "rb")
                        fileopen.seek(int(offset)-1)
                        self.socket_message(CODE_OK)
                        for chunk in self.read_chunk(fileopen, 4096):
                            if 0 < size < 4096:
                                self.buffer_output = self.buffer_output +
                                ("%s %s%s" % (str(size), chunk[0:size], EOL))
                                break
                            self.buffer_output = self.buffer_output +
                            ("%s %s%s" % (str(len(chunk)), chunk[0:size], EOL))
                            size = size - 4096
                        self.buffer_output = self.buffer_output +
                        ('0 %s' % EOL)
                        fileopen.close()
                    else:
                        self.socket_message(BAD_OFFSET)
                except (ValueError, IOError):
                        self.socket_message(INVALID_ARGUMENTS)
                except OSError:
                        self.socket_message(FILE_NOT_FOUND)
            else:
                self.socket_message(INVALID_ARGUMENTS)
        else:
            self.socket_message(INVALID_ARGUMENTS)

    def read_chunk(self, fd, size):
        while True:
            chunk = fd.read(size)
            if not chunk:
                break
            yield

    def socket_message(self, errno):
        self.buffer_output = self.buffer_output +
        ("%s %s" % (errno, error_messages[errno] + EOL))
        if errno in SEND_ERROR:
            self.quit()

    def quit(self):
        self.remove = True
        print 'Listo!'

    def user_program(self, request):
        args = request.split(" ")
        if (len(args) >= 3 and args[0] != 'get_slice'):
            self.socket_message(INVALID_ARGUMENTS)
        else:
            if (args[0] == "get_file_listing"):
                self.get_file_listing()
            elif (args[0] == "get_slice"):
                self.get_slice(request)
            elif (args[0] == "get_metadata"):
                self.get_metadata(request)
            elif (args[0] == "quit"):
                self.quit()
            else:
                self.socket_message(INVALID_COMMAND)
