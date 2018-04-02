#include "node.h"
#include <stdint.h>
#include <string.h>
#include <arpa/inet.h>

#define MAC_SIZE sizeof(MACAddress)
#define ETHERNET 0x0001
#define IP_SIZE sizeof(IPAddress)
#define ipv4 0x0800
#define ARPTYPE 0x0806
#define REQUEST 0x0001
#define REPLY 0x0002

static const MACAddress MAC_BROADCAST = {0x0FF, 0x0FF, 0x0FF, 0x0FF, 0x0FF, 0x0FF};

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
} __attribute__ ((__packed__));;

struct EPacket {
    MACAddress sha; // Dirección de hardware del remitente (Source hardware address)
    MACAddress tha; // Dirección de hardware de destino (Target hardware address)
    uint16_t ethertype;
    char payload[1500];
} __attribute__ ((__packed__));

typedef struct ARPPacket ARPPacket;
typedef struct EPacket EPacket;


int Node::search_ip(IPAddress ip) {
    for (unsigned int i = 0; i <= BOARD_SIZE; i++) {
        if (memcmp(ip_board[i].board_ip, ip, IP_SIZE) == 0) {
            return (i);
        }
    }
    return (-1);
}

void Node::print_ip(IPAddress ip) {
    for (unsigned int x = 0; x<4; x++) {
        printf("%x", ip[x]);
    }
    printf("\n");
}

void Node::print_mac(MACAddress mac) {
    for (unsigned int x = 0; x<6; x++) {
        printf("%x", mac[x]);
    }
    printf("\n");
}

/*
 * Implementar!
 * Intentar enviar `data` al `ip` especificado.
 * `data` es un buffer con IP_PAYLOAD_SIZE bytes.
 * Si la dirección MAC de ese IP es desconocida, debería enviarse un pedido ARP.
 * Devuelve 0 en caso de éxito y distinto de 0 si es necesario reintentar luego
 * (porque se está bucando la dirección MAC usando ARP)
 */
int Node::send_to_ip(IPAddress ip, void *data) {
    EPacket epacket;
    int i = 0;
    i = search_ip(ip);
    MACAddress MY_MAC;
    IPAddress MY_IP;
    get_my_mac_address(MY_MAC);
    get_my_ip_address(MY_IP);
    if (i >= 0) {
        memcpy(epacket.sha, MY_MAC, MAC_SIZE);
        memcpy(epacket.tha, ip_board[i].board_mac, MAC_SIZE);
        epacket.ethertype = htons(ipv4);
        memcpy(epacket.payload, data, IP_PAYLOAD_SIZE);
        send_ethernet_packet(&epacket);
        
        return 0;
    } else {
        ARPPacket arppacket;
        arppacket.htype = htons(ETHERNET);
        arppacket.ptype = htons(ipv4);
        arppacket.hlen = MAC_SIZE;
        arppacket.plen = IP_SIZE;
        arppacket.op = htons(REQUEST);
        memcpy(arppacket.sha, MY_MAC, MAC_SIZE);
        memcpy(arppacket.spa, MY_IP, IP_SIZE);
        memcpy(arppacket.tha, MAC_BROADCAST, MAC_SIZE);
        memcpy(arppacket.tpa, ip, IP_SIZE);
        
        memcpy(epacket.sha, MY_MAC, MAC_SIZE);
        memcpy(epacket.tha, MAC_BROADCAST, MAC_SIZE);
        epacket.ethertype = htons(ARPTYPE);
        memcpy(epacket.payload, &arppacket, IP_PAYLOAD_SIZE);
        
        send_ethernet_packet(&epacket);
        return 1;
    }
}


/*
 * Implementar!
 * Manejar el recibo de un paquete.
 * Si es un paquete ARP: procesarlo.
 * Si es un paquete con datos: pasarlo a la capa de red con receive_ip_packet.
 * `packet` es un buffer de ETHERFRAME_SIZE bytes.
    Un paquete Ethernet tiene:
     - 6 bytes MAC destino
     - 6 bytes MAC origen
     - 2 bytes tipo
     - 46-1500 bytes de payload (en esta aplicación siempre son 1500)
    Tamaño total máximo: 1514 bytes
 */
void Node::receive_ethernet_packet(void *packet) {
    EPacket *etherframe = (EPacket *)(packet);
    int i = 0;
    IPAddress ip;
    MACAddress MY_MAC;
    IPAddress MY_IP;
    get_my_ip_address(MY_IP);
    get_my_mac_address(MY_MAC);

    if ((ntohs(etherframe->ethertype)) == ARPTYPE) {
        ARPPacket *arppacket = (ARPPacket *)(etherframe->payload);
            memcpy(ip, arppacket->spa, IP_SIZE);
            bool merge_flag = false;
            i = search_ip(ip);
            if (i >= 0) {
                memcpy(ip_board[i].board_mac, arppacket->sha, MAC_SIZE);
                merge_flag = true;
            }
            if (memcmp(MY_IP, arppacket->tpa, IP_SIZE) == 0) {
                if (!merge_flag) {
                    memcpy(ip_board[BOARD_SIZE].board_mac, arppacket->sha, MAC_SIZE);
                    memcpy(ip_board[BOARD_SIZE].board_ip, arppacket->spa, IP_SIZE);
                    BOARD_SIZE++;
                }
                if (ntohs(arppacket->op) == REQUEST) {
                    memcpy(arppacket->tha, arppacket->sha, MAC_SIZE);
                    memcpy(arppacket->sha, MY_MAC, MAC_SIZE);
                    memcpy(arppacket->tpa, arppacket->spa, IP_SIZE);
                    memcpy(arppacket->spa, MY_IP, IP_SIZE);
                    arppacket->op = htons(REPLY);

                    memcpy(etherframe->tha, etherframe->sha, MAC_SIZE);
                    memcpy(etherframe->sha, MY_MAC, MAC_SIZE);
                    etherframe->ethertype = htons(ARPTYPE);
                    memcpy(etherframe->payload, arppacket, IP_PAYLOAD_SIZE);
                    send_ethernet_packet(etherframe);
                }
            }
    } else {
        if (memcmp(etherframe->tha, MY_MAC, MAC_SIZE) == 0) {
            receive_ip_packet(etherframe->payload);
        }
    }
}


/*
 * Constructor de la clase. Poner inicialización aquí.
 */
Node::Node() {
    BOARD_SIZE = 0;
    for (unsigned int i = 0; i < 256; i++) {
        memset(ip_board[i].board_ip, 0, IP_SIZE);
        memset(ip_board[i].board_mac, 0, MAC_SIZE);
    }
    timer = NULL;
    for (unsigned int i = 0; i != AMOUNT_OF_CLIENTS; ++i) {
        seen[i] = 0;
    }
}
