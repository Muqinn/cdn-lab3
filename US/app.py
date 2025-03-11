import socket
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)
US_PORT = 8080

def query_authoritative(as_ip, as_port, hostname):
    query = (
        f"TYPE=A\n"
        f"NAME={hostname}\n"
    )
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.settimeout(5) 
    try:
        udp_sock.sendto(query.encode(), (as_ip, int(as_port)))
        data, _ = udp_sock.recvfrom(1024)
        response = data.decode()
        for line in response.splitlines():
            if line.startswith("VALUE="):
                _, ip_val = line.split("=", 1)
                return ip_val.strip()
    except socket.timeout:
        return None
    finally:
        udp_sock.close()
    return None

@app.route('/fibonacci', methods=['GET'])
def user_fibonacci():
    hostname = request.args.get("hostname")
    fs_port = request.args.get("fs_port")
    number = request.args.get("number")
    as_ip = request.args.get("as_ip")
    as_port = request.args.get("as_port")

    if not all([hostname, fs_port, number, as_ip, as_port]):
        return jsonify({"error": "Missing one or more required parameters"}), 400

    resolved_ip = query_authoritative(as_ip, as_port, hostname)
    if resolved_ip is None:
        return jsonify({"error": "Could not resolve hostname via AS"}), 500

    fs_url = f"http://{resolved_ip}:{fs_port}/fibonacci"
    try:
        fs_response = requests.get(fs_url, params={"number": number})
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Error contacting Fibonacci Server: {str(e)}"}), 500

    if fs_response.status_code != 200:
        return jsonify({"error": "Fibonacci Server returned an error"}), fs_response.status_code

    return jsonify(fs_response.json()), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=US_PORT, debug=True)
