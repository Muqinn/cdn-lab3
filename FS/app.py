import socket
import json
from flask import Flask, request, jsonify

app = Flask(__name__)

FS_PORT = 9090  


REGISTERED = False
FS_CONFIG = {}

def send_udp_registration(as_ip, as_port, hostname, ip_address):
    message = (
        f"TYPE=A\n"
        f"NAME={hostname}\n"
        f"VALUE={ip_address}\n"
        f"TTL=10\n"
    )
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.sendto(message.encode(), (as_ip, int(as_port)))
    
    print(f"[FS] Sent registration message to AS at {as_ip}:{as_port}:\n{message}")
    udp_sock.close()

@app.route('/register', methods=['PUT'])
def register():
    global REGISTERED, FS_CONFIG
    data = request.get_json()
    required_keys = ["hostname", "ip", "as_ip", "as_port"]
    if not data or any(k not in data for k in required_keys):
        return jsonify({"error": "Missing registration parameters"}), 400

    hostname = data["hostname"]
    ip_address = data["ip"]
    as_ip = data["as_ip"]
    as_port = data["as_port"]

    FS_CONFIG = {"hostname": hostname, "ip": ip_address, "as_ip": as_ip, "as_port": as_port}

    
    send_udp_registration(as_ip, as_port, hostname, ip_address)
    REGISTERED = True

    return jsonify({"message": f"Registered {hostname} with AS"}), 201

@app.route('/fibonacci', methods=['GET'])
def get_fibonacci():
    
    num_str = request.args.get("number")
    if num_str is None:
        return jsonify({"error": "Missing number parameter"}), 400
    try:
        n = int(num_str)
    except ValueError:
        return jsonify({"error": "Parameter 'number' must be an integer"}), 400

    
    def compute_fib(n):
        if n < 0:
            return None
        a, b = 0, 1
        for _ in range(n):
            a, b = b, a + b
        return a

    result = compute_fib(n)
    return jsonify({"number": n, "fibonacci": result}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=FS_PORT, debug=True)