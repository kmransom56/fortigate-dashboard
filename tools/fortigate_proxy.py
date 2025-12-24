#!/usr/bin/env python3
"""
Simple HTTP/HTTPS proxy to forward FortiGate API requests from Docker container to host network.
This solves the Docker Desktop networking limitation where containers can't access host's physical network.
"""
import socket
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

FORTIGATE_HOST = "192.168.0.254"
FORTIGATE_PORT = 443
PROXY_PORT = 8443


class FortiGateProxyHandler(BaseHTTPRequestHandler):
    def do_CONNECT(self):
        """Handle HTTPS CONNECT requests"""
        host, port = self.path.split(":")
        port = int(port)
        
        try:
            # Connect to FortiGate
            fortigate_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            fortigate_sock.connect((FORTIGATE_HOST, FORTIGATE_PORT))
            
            # Send connection established
            self.wfile.write(b"HTTP/1.1 200 Connection established\r\n\r\n")
            
            # Forward data bidirectionally
            self.forward_data(self.connection, fortigate_sock)
        except Exception as e:
            self.send_error(502, f"Proxy error: {e}")
    
    def forward_data(self, client_sock, server_sock):
        """Forward data between client and server"""
        def forward(src, dst):
            try:
                while True:
                    data = src.recv(4096)
                    if not data:
                        break
                    dst.sendall(data)
            except:
                pass
            finally:
                src.close()
                dst.close()
        
        t1 = threading.Thread(target=forward, args=(client_sock, server_sock))
        t2 = threading.Thread(target=forward, args=(server_sock, client_sock))
        t1.start()
        t2.start()
        t1.join()
        t2.join()
    
    def do_GET(self):
        """Handle HTTP GET requests (for testing)"""
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(f"FortiGate Proxy running. Target: {FORTIGATE_HOST}:{FORTIGATE_PORT}".encode())


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PROXY_PORT), FortiGateProxyHandler)
    print(f"FortiGate proxy listening on 0.0.0.0:{PROXY_PORT}")
    print(f"Forwarding to {FORTIGATE_HOST}:{FORTIGATE_PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down proxy...")
        server.shutdown()
