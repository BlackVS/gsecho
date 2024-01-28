#!/usr/bin/env python3

import argparse
import socket
import ssl
import threading
import time

# Shared variables for statistics
success_count = 0
failure_count = 0
lock = threading.Lock()

def tcp_client(server_ip, server_port, data):
    # print(f"Sending {len(data)} bytes")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((server_ip, server_port))
            s.sendall(data)

            response = b''

            s.setblocking(False)  # Set the socket to non-blocking mode
            s.settimeout(2)

            expected_length = len(data)
            while len(response) < expected_length:
                # print(f"Total received {len(response)} bytes")

                try:
                    packet = s.recv(1024)
                    if packet:
                        response += packet
                        # print(f"Received {len(packet)} bytes")
                except BlockingIOError:
                    time.sleep(0.1)  # Sleep and try again for non-blocking reads

        # print("Exit from tcp_client")
        return response
    except Exception as e:
        print(f"TCP client error: {e}")
        return None
    

def tls_client(server_ip, server_port, data, certfile):
    try:
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=certfile)
        context.check_hostname = False  # Disable hostname verification
        context.verify_mode = ssl.CERT_NONE  # Disable certificate verification
        with socket.create_connection((server_ip, server_port)) as sock:
            with context.wrap_socket(sock, server_hostname=server_ip) as ssock:
                ssock.sendall(data)

                response = b''
                ssock.setblocking(False)  # Set the socket to non-blocking mode
                ssock.settimeout(2)

                expected_length = len(data)
                while len(response) < expected_length:
                    try:
                        packet = ssock.recv(1024)
                        if packet:
                            response += packet
                    except BlockingIOError:
                        time.sleep(0.1)  # Sleep and try again for non-blocking reads

        return response
    except Exception as e:
        print(f"TLS client error: {e}")
        return None

    

def udp_client(server_ip, server_port, data, mtu):
    effective_mtu = mtu - 28  # Adjust for IP and UDP headers
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setblocking(False)  # Set socket to non-blocking mode
        chunks = [data[i:i + effective_mtu] for i in range(0, len(data), effective_mtu)]
        responses = bytearray()
        total_sent = 0

        for chunk in chunks:
            s.sendto(chunk, (server_ip, server_port))
            total_sent += len(chunk)
            try:
                while True:  # Read all available responses
                    response, _ = s.recvfrom(65536)
                    responses.extend(response)
            except BlockingIOError:
                pass  # No more data available to read

        s.setblocking(True)  # Set socket back to blocking mode
        s.settimeout(2.0)  # Set a timeout for final receives

        # Wait for any remaining responses
        while len(responses) < total_sent:
            try:
                response, _ = s.recvfrom(65536)
                responses.extend(response)
            except socket.timeout:
                break  # Exit if no more responses are received

        return responses

def send_data(protocol, server_ip, server_port, data, certfile=None, mtu=1500):
    if protocol == 'tcp':
        return tcp_client(server_ip, server_port, data)
    elif protocol == 'tls':
        return tls_client(server_ip, server_port, data, certfile)
    elif protocol == 'udp':
        return udp_client(server_ip, server_port, data, mtu)
    else:
        raise ValueError("Invalid protocol")

def worker_thread(protocol, server_ip, server_port, data, certfile, mtu):
    global success_count, failure_count

    response = send_data(protocol, server_ip, server_port, data, certfile, mtu)
    # print(f"Response: {response}")
    
    with lock:
        if response == data:
            success_count += 1
        else:
            failure_count += 1
            print(f"Data mismatch or no response. Sent: {data}, Received: {response}")  # Debugging line

def main():
    parser = argparse.ArgumentParser(description="Echo Client")
    parser.add_argument("--protocol", choices=['tcp', 'tls', 'udp'], required=True)
    parser.add_argument("--server_ip", required=True)
    parser.add_argument("--server_port", type=int, required=True)
    parser.add_argument("--file", help="File to send")
    parser.add_argument("--text", help="Text to send")
    parser.add_argument("--threads", type=int, default=1)
    parser.add_argument("--certfile", help="Certificate file for TLS")
    parser.add_argument("--mtu", type=int, default=1500, help="MTU size for UDP transmission (default: 1500)")
    args = parser.parse_args()

    if args.file:
        with open(args.file, 'rb') as f:
            data = f.read()
    elif args.text:
        data = args.text.encode()
    else:
        raise ValueError("Either --file or --text must be specified")

    threads = []
    for _ in range(args.threads):
        thread = threading.Thread(target=worker_thread, args=(args.protocol, args.server_ip, args.server_port, data, args.certfile, args.mtu))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    print(f"SUCCESS: {success_count} times")
    print(f"FAILED : {failure_count} times")

if __name__ == "__main__":
    main()
