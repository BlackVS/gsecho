#!/usr/bin/env python3

import sys
import argparse
from twisted.internet import ssl, reactor, protocol
from twisted.internet.protocol import DatagramProtocol, Factory

# Echo server classes
class EchoTCP(protocol.Protocol):
    def connectionMade(self):
        client = self.transport.getPeer()
        print(f"TCP Connection from: {client.host}:{client.port}")

    def dataReceived(self, data):
        self.transport.write(data)

class EchoTLS(EchoTCP):
    def connectionMade(self):
        client = self.transport.getPeer()
        print(f"TLS Connection from: {client.host}:{client.port}")

class EchoUDP(DatagramProtocol):
    def datagramReceived(self, data, addr):
        print(f"UDP Packet from: {addr[0]}:{addr[1]}")
        self.transport.write(data, addr)

# Argument parsing
def parse_args():
    parser = argparse.ArgumentParser(description="Twisted Echo Servers")
    parser.add_argument("--tcp", type=int, help="Enable TCP Echo Server on the specified port")
    parser.add_argument("--tls", type=int, help="Enable TLS Echo Server on the specified port")
    parser.add_argument("--udp", type=int, help="Enable UDP Echo Server on the specified port")
    return parser.parse_args()

# Start servers based on arguments
def start_servers(args):
    if args.tcp:
        tcpFactory = Factory()
        tcpFactory.protocol = EchoTCP
        reactor.listenTCP(args.tcp, tcpFactory)
        print(f"TCP Echo Server is running on port {args.tcp}")

    if args.tls:
        tlsFactory = Factory()
        tlsFactory.protocol = EchoTLS
        with open("server.pem") as certFile:
            certificate = ssl.PrivateCertificate.loadPEM(certFile.read())
        reactor.listenSSL(args.tls, tlsFactory, certificate.options())
        print(f"TLS Echo Server is running on port {args.tls}")

    if args.udp:
        reactor.listenUDP(args.udp, EchoUDP())
        print(f"UDP Echo Server is running on port {args.udp}")

    if not (args.tcp or args.tls or args.udp):
        print("No protocol specified. Use --tcp, --tls, or --udp to start respective servers.")
        sys.exit(1)

    reactor.run()

# Main execution
if __name__ == "__main__":
    args = parse_args()
    start_servers(args)
