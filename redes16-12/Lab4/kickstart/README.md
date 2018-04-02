Laboratorio 4 - Proxy HTTP
===========
La tarea a realizar en este laboratorio fue implementar un proxy HTTP reverso para balancear la carga de un servidor. Esto quiere decir que el proxy es un intermediario entre cliente y servidor, es decir, que el cliente ve al proxy como servidor y el servidor lo ve como cliente.

#Estructuracion del servidor

Al correr el proyecto se ejecuta la funciÃ³n run del proxy, la cual maneja los datos de las conexiones con las funciones *handle_ready* y *handle_events* y al final cierra las conexiones con la funciÃ³n *remove_finished*.

**Forward**
Clase cuya funciÃ³n es copiar todo lo que envÃ­a una conexiÃ³n emisora y mandarlo a otra conexiÃ³n destino

**RequestHandlerTask**
En esta clase se parsea el request hecho por el cliente y se crea una nueva conexiÃ³n con el host deseado a la que se le copia el request hecho por el cliente, a esta ultima conexiÃ³n se le asigna la tarea de Forward.
A una conexiÃ³n se le asignara de tarea RequestHandlerTask cuando se acepta una nueva conexiÃ³n.

#Decisiones de diseÃ±o tomadas

Se decidiÃ³ que para balancear la carga entre los servidores de cada host se eligiese una direcciÃ³n ip al azar, esto se hace con la funciÃ³n auxiliar *connect_to_random_ip* que toma al susodicho host, y elige una direcciÃ³n ip al azar de el mapa de hosts que tiene el proxy a donde conectar el socket.

Se le agrego al Proxy la siguiente linea:
```python
master_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
```
para que se pudiese reutilizar el mismo puerto al finalizar una conexiÃ³n.

El resto de las funciones tenÃ­an una especificaciÃ³n bastante completa que seguir.

#Dificultades

Una de las dificultades fue entender bien como eran los **request** del cliente al servidor para poder reenviarlos de la misma manera al mismo, lo que se hizo para solucionar este problema fue aÃ±adir prints de cada **request** que era enviada por el cliente para poder recrearla lo mejor posible.

Otra dificultad fue darse cuenta que la funciÃ³n *parse_headers* implementada por la cÃ¡tedra devolvÃ­a la segunda parte del header con un espacio al comienzo. p.e:
Head: ' www.famaf.unc.edu.ar', por lo cual, al buscar ese host en el mapa de hosts del proxy no encontraba nada. Otra vez el error se hizo evidente con los prints que mostraban como eran los headers.

