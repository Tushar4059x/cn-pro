import socket
import threading
import datetime

def handle_client(conn, addr):
    print(f"Connected by {addr}")
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            
            # Log packet size and timestamp to traffic_log.txt
            packet_size = len(data)
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log_entry = f"{timestamp},{packet_size}\n"
            
            try:
                with open('traffic_log.txt', 'a') as log_file:
                    log_file.write(log_entry)
            except Exception as e:
                print(f"Error writing to log file: {e}")
            
            print(f"Received: {data.decode()}")
            print(f"Logged: {log_entry.strip()}")
            conn.sendall(data)
    except ConnectionResetError:
        print(f"Connection with {addr} closed by client.")
    finally:
        conn.close()

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('127.0.0.1', 12345))
    server_socket.listen()

    print("Server listening on 127.0.0.1:12345")

    while True:
        conn, addr = server_socket.accept()
        client_thread = threading.Thread(target=handle_client, args=(conn, addr))
        client_thread.start()

if __name__ == "__main__":
    start_server()