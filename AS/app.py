import socket
import json
import os

DNS_FILE = "dns_records.json"
UDP_PORT = 53533


if os.path.exists(DNS_FILE):
    with open(DNS_FILE, "r") as f:
        dns_records = json.load(f)
else:
    dns_records = {}

def save_records():
    with open(DNS_FILE, "w") as f:
        json.dump(dns_records, f)

def parse_message(message):
    """Parses the incoming message into a dict.
       Expects lines like 'KEY=VALUE'
    """
    result = {}
    lines = message.strip().splitlines()
    for line in lines:
        if '=' in line:
            key, value = line.split("=", 1)
            result[key.strip()] = value.strip()
    return result

def build_response(record):
    """Builds a DNS response message from a record dict."""
    response_lines = [
        f"TYPE=A",
        f"NAME={record['NAME']}",
        f"VALUE={record['VALUE']}",
        f"TTL={record['TTL']}"
    ]
    return "\n".join(response_lines) + "\n"


sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('0.0.0.0', UDP_PORT))
print(f"[AS] Listening for UDP messages on port {UDP_PORT}...")

while True:
    data, addr = sock.recvfrom(1024)
    message = data.decode()
    print(f"[AS] Received message from {addr}:\n{message}")
    msg_dict = parse_message(message)

    
    if "VALUE" in msg_dict:
        hostname = msg_dict.get("NAME")
        ip_address = msg_dict.get("VALUE")
        ttl = msg_dict.get("TTL", "10")
        if hostname and ip_address:
            
            dns_records[hostname] = {"NAME": hostname, "VALUE": ip_address, "TYPE": "A", "TTL": ttl}
            save_records()
            print(f"[AS] Registered {hostname} -> {ip_address}")
        
        ack = f"Registered {hostname}\n"
        sock.sendto(ack.encode(), addr)

    
    elif "NAME" in msg_dict and "TYPE" in msg_dict:
        hostname = msg_dict.get("NAME")
        if hostname in dns_records:
            record = dns_records[hostname]
            response = build_response(record)
            print(f"[AS] Responding with record:\n{response}")
            sock.sendto(response.encode(), addr)
        else:
            error_response = "Error: Record not found\n"
            print(f"[AS] {error_response}")
            sock.sendto(error_response.encode(), addr)
    else:
        error = "Error: Malformed message\n"
        print(f"[AS] {error}")
        sock.sendto(error.encode(), addr)