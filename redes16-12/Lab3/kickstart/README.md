#Informe del laboratorio 3.#

##Implementación de un protocolo ARP -- RFC 826

####**Objetivo**

El objetivo de este laboratiorio consiste en implementar el protocolo RFC826 "An Ethernet Address Resolution Protocol". Para esto, se debían completar dos funciones: 
* send_to_ip
* receive_ethernet_packet

####**Implementación**

__Estructuras de los paquetes__

Primero se implementaron los tipos de datos de los paquetes, respectivamente el paquete ARP y Ethernet:
```
struct ARPPacket {
    uint16_t htype; // Tipo del hardware
    uint16_t ptype; // Tipo del protocolo
    uint8_t hlen;  // Largo del hardware (8 bits)
    uint8_t plen; // Largo del protocolo (8 bits)
    uint16_t op;  // operación que el emisor está realizando: 1 para la petición, 2 para la respuesta.
    MACAddress sha; // Dirección de hardware del remitente (Source hardware address)
    IPAddress spa; // Direccion remitente de protocolo (Source protocol address)
    MACAddress tha; // Dirección de hardware de destino (Target hardware address)
    IPAddress tpa; // Dirección de protocolo de destino (Target protocol address)
} __ attribute __ ((__ packed __));;


struct EPacket {
    MACAddress sha; // Dirección de hardware del remitente (Source hardware address)
    MACAddress tha; // Dirección de hardware de destino (Target hardware address)
    uint16_t ethertype;
    char payload[1500];
} __ attribute __ ((__ packed __));

```

Se les aplico el atributo __packed__ para que al enviarse los paquetes no se leyeran de forma separada los bytes, es decir que siempre se mantengan empaquetados los bytes.

**La tabla de direcciones:**

Primero se implementó la tabla de direcciones como un array que contenía 255 posiciones y que guardaba en cada una de ellas una dirección Mac, en caso de conocer el IP, o 0, en caso de no conocer el IP.

Luego se decidió cambiar la implementación por una mas efectiva que fue creando el tipo ***board*** que almacena una dirección IP y una dirección Mac, y luego se crea un arreglo que tiene 255 celdas de susodicho tipo.

**Funciones**

La función **send_to_ip** recibe un paquete y una dirección ip a la cual se desea enviarlo, primero se fija si se conoce dicha dirección (Esto se hace mediante una función llamada search_ip, que busca una dirección ip dentro de una tabla),
si se conoce la dirección ip, entonces se arma el paquete ethernet o "Ethernet Frame". Si no se conoce la dirección ip, entonces se arma un paquete ARP que luego se guarda dentro de un Ethernet frame y se lo envía a la dirección Mac broadcast.

La función **receive_ethernet_packet** recibe un paquete y se fija si es de tipo ARP o no.
* Si es de tipo IP entonces se envia el paquete a la capa de red
* Si es de tipo ARP entonces se pregunta si el paquete habla el mismo protocolo (en este caso es 0x0800), si lo hace, se pregunta si se tiene la dirección ip almacenada en la tabla de direcciones, si está, entonces se actualiza la dirección Mac, si no esta entonces se pregunta si quien recibe el paquete es el destinatario, si lo es entonces genera una nueva entrada en la tabla de direcciones con ambas direcciones (la Mac y la IP). Por último se checkea el código de operación del paquete ARP, si el mismo es de tipo REQUEST, entonces se arma un paquete ARP y se lo mete dentro del payload de un Ethernet frame, el cual será enviado a la dirección de quien mando el paquete ARP.

**Funciones auxiliares**

Se creó una función auxiliar llamada **search_ip**, que lo que hace es, dado un ip, se fija si esta en la tabla de direcciones y, si está, retorna la posición de la tabla en la cual se encuentra, si no está retorna 0.

**Librerías**

* **arpa/inet.h**: Fue necesaria debido a que contiene las funciones htons y ntohs que sirven para que el programa funcione en distintas computadoras, ya que debido a la endiannes de cada una, los enteros se pueden tomar de distinta manera, estas funciones previenen eso.
* **stdint.h**: Fue necesaria para poder usar los tipos uint16_t y uint8_t dentro de las estructuras de los paquetes.
* **string.h**: Fue necesaria para poder usar las funciones memcpy, memset y memcmp, ya que no se pueden asignar los valores de las direcciones.

**Dificultades**

* La cantidad de condicionales dentro de la función receive_ethernet_package fue una gran confusión
* En omnet resulta muy difícil encontrar los errores y donde se encuentran