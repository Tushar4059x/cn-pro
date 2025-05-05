# Network Traffic Congestion Visualization

A real-time network traffic monitoring and visualization system that generates customizable traffic patterns, captures network metrics, and visualizes congestion in real-time.

![Network Traffic Visualization](https://example.com/visualization.png)

## 📌 Project Overview

This project creates a comprehensive system to visualize network traffic congestion in real-time, helping to understand how traffic patterns affect network metrics like TCP Window Size, Round Trip Time (RTT), and overall throughput.

### Key Features

- **Configurable Traffic Generator**: Create various traffic patterns with bursts to simulate real-world scenarios
- **Real-time Data Visualization**: Monitor multiple network metrics simultaneously
- **Congestion Detection**: Visual alerts when congestion thresholds are exceeded
- **Customizable Parameters**: Adjust settings for different network conditions

## 🏗️ System Architecture

The system consists of three main components that work together:

### 1. Server (`server.py`)
- Simple TCP server that listens on 127.0.0.1:12345
- Receives data from clients and echoes it back
- Logs traffic details to `traffic_log.txt`

### 2. Client (`client.py`)
- Configurable traffic generator that connects to the server
- Capable of creating both steady traffic and burst patterns
- Highly customizable message sizes and intervals

### 3. Visualizer (`live_visualizer.py`)
- Captures and analyzes network packets using pyshark
- Extracts and processes TCP metrics in real-time
- Displays interactive, multi-panel visualization
- Highlights congestion events

## 🔧 Installation

### Prerequisites
- Python 3.7 or higher
- Wireshark (for packet capture)

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/Tushar4059x/cn-pro
   cd cn-pro
   ```

2. **Create and activate a virtual environment (recommended)**
   ```bash
   python -m venv cnpro_env
   source cnpro_env/bin/activate  # On Windows: env\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install pyshark matplotlib numpy
   ```

4. **Install Wireshark**
   - macOS: `brew install wireshark`
   - Ubuntu/Debian: `sudo apt install wireshark`
   - Windows: Download from [Wireshark.org](https://www.wireshark.org/)

## 🚀 Usage

The components must be started in the correct order:

### 1. Start the Server
```bash
python server.py
```

### 2. Start the Visualizer
```bash
# Important: Use display filter syntax with "tcp.port == 12345" (not "tcp port 12345")
python live_visualizer.py --interface lo0 --filter "tcp.port == 12345"
```

> **Note for different operating systems:**
> - macOS: Use interface `lo0`
> - Linux: Use interface `lo`
> - Windows: Use your loopback interface name (typically `loopback`)

### 3. Run the Client
```bash
python client.py
```

## 🎛️ Configuration Options

### Visualizer Options
| Parameter | Description | Default |
|-----------|-------------|---------|
| `--interface` | Network interface to capture packets from | `lo0` |
| `--filter` | Display filter for packet capture (use TShark display filter syntax) | `tcp` |
| `--history` | Number of data points to keep in history | `100` |
| `--interval` | Refresh interval in milliseconds | `100` |
| `--rtt-threshold` | RTT threshold in ms for congestion detection | `100.0` |
| `--cwnd-threshold` | CWND threshold as fraction of max for congestion detection | `0.7` |

### Client Options
| Parameter | Description | Default |
|-----------|-------------|---------|
| `--base-interval` | Base time interval between messages in seconds | `0.5` |
| `--min-interval` | Minimum time interval between messages in seconds | `0.1` |
| `--burst-probability` | Probability of sending a burst of messages (0-1) | `0.1` |
| `--burst-messages` | Number of messages to send in a burst | `10` |
| `--burst-interval` | Time interval between messages during a burst | `0.01` |
| `--min-size` | Minimum message size in bytes | `10` |
| `--max-size` | Maximum message size in bytes | `1024` |

## 📊 Visualization Panels

The visualization window displays four panels of real-time metrics:

1. **TCP Window Size** (top left): 
   - Larger window sizes indicate better network capacity
   - Sudden drops suggest congestion

2. **Round Trip Time (RTT)** (top right):
   - Higher RTT values indicate network delay
   - Spikes often correlate with congestion events

3. **Network Throughput** (middle):
   - Shows packets processed per second
   - Drops in throughput indicate potential congestion

4. **Congestion Indicator** (bottom):
   - Combined metric calculated from RTT and window size
   - Red highlights indicate when congestion is detected

## ⚠️ Troubleshooting

### Visualizer Issues

#### Empty Charts or No Data
- Ensure you're using the correct **display filter syntax**: `tcp.port == 12345` (not `tcp port 12345`)
- Check that the server and client are running and communicating
- Verify you're using the correct network interface

#### TShark Crashes
- Use display filter syntax (`tcp.port == 12345`) instead of capture filter syntax (`tcp port 12345`)
- Check that Wireshark/TShark is properly installed
- Try running with elevated permissions if necessary

#### Missing Dependencies
- Ensure all required packages are installed: `pip install pyshark matplotlib numpy`

### Connection Issues
- Confirm the server is running before starting the client
- Check if port 12345 is already in use with: `lsof -i :12345`
- Verify no firewall rules are blocking the connection

### Performance Issues
- Reduce history length: `--history 50`
- Increase update interval: `--interval 200`
- Close other applications consuming system resources

## 🔍 Advanced Usage

### Creating Custom Traffic Patterns

For video streaming simulation:
```bash
python client.py --min-size 1000 --max-size 10000 --burst-probability 0.2 --burst-messages 50
```

For bursty web traffic:
```bash
python client.py --base-interval 1.0 --burst-probability 0.4 --burst-messages 15 --min-size 500 --max-size 2000
```

### Running on Different Networks

To monitor traffic between different machines:
1. Modify server.py to bind to a specific IP
2. Update client.py to connect to that IP
3. Run the visualizer on one of the machines with appropriate interface settings

## 🔮 Future Improvements

Planned enhancements to the system:

1. **Additional Metrics**: Packet loss rate, jitter, and connection statistics
2. **Protocol Support**: UDP, ICMP, and application-layer protocol analysis
3. **Traffic Pattern Templates**: Pre-configured scenarios for different use cases
4. **Distributed Testing**: Multi-client traffic generation and analysis
5. **Recording and Playback**: Save and replay captured data
6. **Statistical Analysis**: Advanced congestion detection algorithms
7. **Alert System**: Notifications based on user-defined thresholds

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.
