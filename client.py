import socket
import time
import random
import string
import argparse

def generate_random_string(min_size=10, max_size=1024):
    """Generate a random string of random length between min_size and max_size."""
    size = random.randint(min_size, max_size)
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(size))

def send_messages(base_interval=0.5, min_interval=0.1, burst_probability=0.1, 
                  burst_messages=10, burst_interval=0.01, min_size=10, max_size=1024):
    """
    Send random traffic to the server continuously.
    
    Args:
        base_interval (float): Base time interval between messages in seconds
        min_interval (float): Minimum time interval between messages in seconds
        burst_probability (float): Probability of sending a burst of messages (0-1)
        burst_messages (int): Number of messages to send in a burst
        burst_interval (float): Time interval between messages during a burst
        min_size (int): Minimum message size in bytes
        max_size (int): Maximum message size in bytes
    """
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('127.0.0.1', 12345))
    
    message_count = 0
    
    try:
        print("Starting to send messages. Press Ctrl+C to stop.")
        while True:  # Run indefinitely until interrupted
            # Decide whether to send a burst of messages or a single message
            if random.random() < burst_probability:
                print(f"Sending burst of {burst_messages} messages...")
                # Send a burst of messages
                for _ in range(burst_messages):
                    message = f"Message {message_count}: {generate_random_string(min_size, max_size)}"
                    client_socket.sendall(message.encode())
                    message_count += 1
                    time.sleep(burst_interval)  # Very small delay during burst
            else:
                # Send a single message with random content
                message = f"Message {message_count}: {generate_random_string(min_size, max_size)}"
                client_socket.sendall(message.encode())
                message_count += 1
                
                # Random interval between messages, but at least min_interval
                interval = max(min_interval, random.uniform(min_interval, base_interval))
                time.sleep(interval)
                
            # Print status every 100 messages
            if message_count % 100 == 0:
                print(f"Sent {message_count} messages so far")
                
    except KeyboardInterrupt:
        print(f"\nStopping after sending {message_count} messages")
    finally:
        client_socket.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Network Traffic Generator Client')
    parser.add_argument('--base-interval', type=float, default=0.5,
                        help='Base time interval between messages in seconds (default: 0.5)')
    parser.add_argument('--min-interval', type=float, default=0.1,
                        help='Minimum time interval between messages in seconds (default: 0.1)')
    parser.add_argument('--burst-probability', type=float, default=0.1,
                        help='Probability of sending a burst of messages (0-1) (default: 0.1)')
    parser.add_argument('--burst-messages', type=int, default=10,
                        help='Number of messages to send in a burst (default: 10)')
    parser.add_argument('--burst-interval', type=float, default=0.01,
                        help='Time interval between messages during a burst (default: 0.01)')
    parser.add_argument('--min-size', type=int, default=10,
                        help='Minimum message size in bytes (default: 10)')
    parser.add_argument('--max-size', type=int, default=1024,
                        help='Maximum message size in bytes (default: 1024)')
    
    args = parser.parse_args()
    
    send_messages(
        base_interval=args.base_interval,
        min_interval=args.min_interval,
        burst_probability=args.burst_probability,
        burst_messages=args.burst_messages,
        burst_interval=args.burst_interval,
        min_size=args.min_size,
        max_size=args.max_size
    )
