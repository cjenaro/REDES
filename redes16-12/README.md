# Laboratorio 1#
En este laboratorio se pidio crear un servidor que pudiese atender a un cliente a la vez y que fuese capaz de proveerle 4 funciones al cliente:

* get_file_listing - devuelve una lista de los archivos en el directorio
* get_metadata - devuelve el tamaño de un archivo
* get_slice - devuelve, a partir de un "offset" de un archivo una cantidad x de bytes
* quit - termina la conexión entre el cliente y el servidor

### server.py ###


Primero se modifico la funcion __init__ en la cual se inicializó el socket usando la función socket.socket, luego se usa socket.bind para asignar al socket una tupla (dirección, puerto) y el después la funcion socket.listen(1) para que se pudiese escuchar de a un cliente.
A continuación en la función serve se acepta la conexión usando socket.accept, la cual te devuelve un socket del cliente y un directorio del cliente con lo que se va a llamar a la función connection.Connection, seguido de la funcion connection.handle la cual sirve para atender a los pedidos del cliente.

### connection.py ###
Lo primero en hacerse en connection.py es modificar la función __init__, donde se le asigna al socket y el directorio del cliente y aparte se le asigna un timeout de 50 segundos usando socket.settimeuot(50) y se le asigna un estado true a la conexión que indica que está conectada, en caso de que el cliente quiera salir, se le asigna false.
Luego se prosiguió a realizar la función handle que va a ser la que va a atender los pedidos del cliente.

Se implementó también una funcion llamada user_program que lo que hace es recibir los comandos que ingresa el cliente y verifica que sean correctos, si lo son, indica que función es la que pidió el cliente y la lleva a cabo.

### Dificultades ###
La mayor dificultad para nuestro grupo, sobre todo siendo que ninguno nunca había usado python anteriormente, es la elección del lenguaje ya que toma tiempo acostumbrarse a un lenguaje nuevo para poder aprovechar todas sus ventajas. Lamentablemente no se pudo lograr que el server pase todos los test. Tenemos problemas con la finalización de linea lo cual nos da varios problemas en los test. Las funciones ahora estan andando pero sin pasar los test.
