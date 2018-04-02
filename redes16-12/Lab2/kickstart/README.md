Informe del laboratorio 2.
=

##Implementación de un servidor asíncrono

####**Objetivo**

El objetivo de este laboratorio fue implementar un servidor asíncrono. Para esto se usó **multiplexación**, más precisamente el modulo select con la función poll(): 

####**Implementación**

Se tomó como base el laboratorio 1 y a partir del mismo se hicieron los cambios:

**Server**

la clase Server, ahora llamada AsyncServer, se modificó para que pueda tomar hasta cinco clientes. Esto se hizo cambiando el socket.listen, que antes era (1) y se cambió por (5). Además se uso la función setblocking(0) para que la comunicación fuese no bloqueante.
	Se prosiguió con la función serve(), en la cual se implementó el objeto poll para tener paralelismo o concurrencia entre los clientes. Iterando por la variable *events* la cual contiene pares (evento, fd) podemos decidir si:
	
* Es un cliente nuevo (el fd es igual al fd del socket del server)
* Si hay que hacer un handle_input() (evento es POLLIN)
* Si hay que hacer un handle_output() (evento es POLLOUT)
* Finalmente, si la conexión se debe terminar (el campo connection.remove es True)

**Connection**

Primero se realizaron cambios en `__init__`, se agregaron las variables `remove`, `buffer_input`y `buffer_output`. Las últimas dos variables son donde se van a almacenar los datos de entrada y salida respectivamente, para procesarlos luego en la función handle correspondiente.

Se implementó la funcion **events()** que devuelve el evento correspondiente dependiendo de si el buffer de salida está vacío o no.

Las funciones **handle_input()** y **handle_output()** se encargan de manejar los datos de entrada y salida respectivamente.

####**Funciones auxiliares**

* valid_filename -- checkea que el nombre del archivo sea válido
* read_chunk -- lee pedazos de un archivo, se usa en la función get_slice
* user_program -- lee los requests y, según el mismo, llama a la función adecuada