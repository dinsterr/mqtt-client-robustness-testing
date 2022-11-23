import monitor.tcp_proxy as tcp_proxy

if __name__ == "__main__":
    tcp_proxy.proxy_socket("localhost", 8088, "localhost", 8081)