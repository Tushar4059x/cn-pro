import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import threading
import pyshark
import time
import numpy as np
import argparse
from collections import deque
import matplotlib.dates as mdates
from matplotlib.gridspec import GridSpec
from matplotlib.patches import Rectangle

class CongestionVisualizer:
    def __init__(self, interface='lo0', display_filter='tcp', history_length=100, 
                 congestion_threshold_rtt=100, congestion_threshold_cwnd=0.7):
        # Create figure with subplots arranged in a grid
        self.fig = plt.figure(figsize=(12, 10))
        self.gs = GridSpec(3, 2, height_ratios=[1, 1, 1], width_ratios=[1, 1])
        
        # Create subplots
        self.ax_cwnd = self.fig.add_subplot(self.gs[0, 0])
        self.ax_rtt = self.fig.add_subplot(self.gs[0, 1])
        self.ax_throughput = self.fig.add_subplot(self.gs[1, :])
        self.ax_congestion = self.fig.add_subplot(self.gs[2, :])
        
        # Set up data storage with fixed buffer size
        self.history_length = history_length
        self.time_values = deque(maxlen=history_length)
        
        # TCP Window Size data
        self.cwnd_values = deque(maxlen=history_length)
        self.max_cwnd = 1000  # Initial value, will be updated
        self.line_cwnd, = self.ax_cwnd.plot([], [], 'b-', linewidth=1.5, label='Window Size')
        
        # RTT data
        self.rtt_values = deque(maxlen=history_length)
        self.line_rtt, = self.ax_rtt.plot([], [], 'g-', linewidth=1.5, label='RTT')
        
        # Throughput data (packets per second)
        self.throughput_values = deque(maxlen=history_length)
        self.packet_count = 0
        self.last_throughput_time = time.time()
        self.line_throughput, = self.ax_throughput.plot([], [], 'r-', linewidth=1.5, label='Throughput')
        
        # Congestion indicator (combined metric)
        self.congestion_values = deque(maxlen=history_length)
        self.congestion_threshold_rtt = congestion_threshold_rtt  # ms
        self.congestion_threshold_cwnd = congestion_threshold_cwnd  # fraction of max
        self.line_congestion, = self.ax_congestion.plot([], [], 'purple', linewidth=1.5, label='Congestion Indicator')
        self.congestion_events = []  # Store times when congestion was detected
        
        # Initialize plots
        self._setup_plots()
        
        # Synchronization
        self.lock = threading.Lock()
        self.start_time = time.time()
        
        # Latest values (updated by capture thread)
        self.latest_cwnd = None
        self.latest_rtt = None
        self.interface = interface
        self.display_filter = display_filter
        
        # Initialize with some dummy data to avoid empty array errors
        self.time_values.append(0)
        self.cwnd_values.append(0)
        self.rtt_values.append(0)
        self.throughput_values.append(0)
        self.congestion_values.append(0)
        
    def _setup_plots(self):
        # Setup TCP Window Size plot
        self.ax_cwnd.set_title('TCP Window Size')
        self.ax_cwnd.set_xlabel('Time (s)')
        self.ax_cwnd.set_ylabel('Window Size')
        self.ax_cwnd.grid(True, alpha=0.3)
        self.ax_cwnd.set_xlim(0, 20)
        self.ax_cwnd.set_ylim(0, self.max_cwnd)
        self.ax_cwnd.legend(loc='upper right')
        
        # Setup RTT plot
        self.ax_rtt.set_title('Round Trip Time (RTT)')
        self.ax_rtt.set_xlabel('Time (s)')
        self.ax_rtt.set_ylabel('RTT (ms)')
        self.ax_rtt.grid(True, alpha=0.3)
        self.ax_rtt.set_xlim(0, 20)
        self.ax_rtt.set_ylim(0, 200)  # Start with 0-200ms range, will auto-adjust
        self.ax_rtt.legend(loc='upper right')
        
        # Setup Throughput plot
        self.ax_throughput.set_title('Network Throughput')
        self.ax_throughput.set_xlabel('Time (s)')
        self.ax_throughput.set_ylabel('Packets per second')
        self.ax_throughput.grid(True, alpha=0.3)
        self.ax_throughput.set_xlim(0, 20)
        self.ax_throughput.set_ylim(0, 100)  # Start with 0-100 pps, will auto-adjust
        self.ax_throughput.legend(loc='upper right')
        
        # Setup Congestion Indicator plot
        self.ax_congestion.set_title('Network Congestion Indicator')
        self.ax_congestion.set_xlabel('Time (s)')
        self.ax_congestion.set_ylabel('Congestion Level (0-1)')
        self.ax_congestion.grid(True, alpha=0.3)
        self.ax_congestion.set_xlim(0, 20)
        self.ax_congestion.set_ylim(0, 1)
        
        # Add a horizontal line at the congestion threshold
        self.congestion_line = self.ax_congestion.axhline(y=0.7, color='r', linestyle='--', alpha=0.7)
        self.ax_congestion.text(0.5, 0.72, 'Congestion Threshold', color='r', fontsize=9)
        self.ax_congestion.legend(loc='upper right')
        
        # Adjust layout
        self.fig.tight_layout()
        self.fig.suptitle('Network Traffic Congestion Monitor', fontsize=16)
        self.fig.subplots_adjust(top=0.92)
    
    def calculate_congestion(self, rtt, cwnd):
        """Calculate a congestion indicator based on RTT and CWND."""
        if rtt is None or cwnd is None:
            return None
            
        # Normalize RTT (higher is worse)
        norm_rtt = min(1.0, rtt / self.congestion_threshold_rtt)
        
        # Normalize CWND (lower is worse)
        if self.max_cwnd > 0:
            norm_cwnd = 1.0 - min(1.0, cwnd / self.max_cwnd)
        else:
            norm_cwnd = 0
            
        # Combined metric (simple average)
        return (norm_rtt + norm_cwnd) / 2
    
    def update_plot(self, frame):
        current_time = time.time() - self.start_time
        is_congested = False
        
        with self.lock:
            # Calculate throughput
            packets_since_last = self.packet_count
            self.packet_count = 0
            time_elapsed = current_time - self.last_throughput_time
            if time_elapsed > 0:
                throughput = packets_since_last / time_elapsed
                self.throughput_values.append(throughput)
                self.last_throughput_time = current_time
            
            # Update time values
            self.time_values.append(current_time)
            
            # Update window size if available
            if self.latest_cwnd is not None:
                self.cwnd_values.append(self.latest_cwnd)
                # Update max window size seen
                if self.latest_cwnd > self.max_cwnd:
                    self.max_cwnd = self.latest_cwnd
                    self.ax_cwnd.set_ylim(0, self.max_cwnd * 1.1)
            else:
                # Maintain the array size
                self.cwnd_values.append(None)
            
            # Update RTT if available
            if self.latest_rtt is not None:
                self.rtt_values.append(self.latest_rtt)
                # Auto-adjust y-axis if needed
                if self.latest_rtt > self.ax_rtt.get_ylim()[1]:
                    self.ax_rtt.set_ylim(0, self.latest_rtt * 1.5)
            else:
                # Maintain the array size
                self.rtt_values.append(None)
            
            # Calculate congestion indicator
            congestion = self.calculate_congestion(self.latest_rtt, self.latest_cwnd)
            if congestion is not None:
                self.congestion_values.append(congestion)
                # Check if we're in a congested state
                if congestion > 0.7:  # Threshold for congestion
                    is_congested = True
                    self.congestion_events.append(current_time)
            else:
                # Maintain the array size
                self.congestion_values.append(None)
        
        # Update plots
        time_list = list(self.time_values)
        
        # Update TCP Window Size plot
        self.line_cwnd.set_data(time_list, list(self.cwnd_values))
        self.ax_cwnd.relim()
        self.ax_cwnd.autoscale_view(scalex=True, scaley=False)
        
        # Update RTT plot
        self.line_rtt.set_data(time_list, list(self.rtt_values))
        self.ax_rtt.relim()
        self.ax_rtt.autoscale_view(scalex=True, scaley=False)
        
        # Update Throughput plot
        self.line_throughput.set_data(time_list, list(self.throughput_values))
        self.ax_throughput.relim()
        self.ax_throughput.autoscale_view(scalex=True, scaley=True)
        
        # Update Congestion Indicator plot
        self.line_congestion.set_data(time_list, list(self.congestion_values))
        self.ax_congestion.relim()
        self.ax_congestion.autoscale_view(scalex=True, scaley=False)
        
        # Add red background for congestion events
        if is_congested:
            for ax in [self.ax_cwnd, self.ax_rtt, self.ax_throughput, self.ax_congestion]:
                # Add a red vertical bar for the current time
                ax.axvspan(current_time-0.5, current_time, alpha=0.3, color='red')
        
        # Adjust x-axis limits to show the latest data
        if time_list:
            x_min = max(0, time_list[-1] - 20)  # Show last 20 seconds
            x_max = time_list[-1] + 1
            for ax in [self.ax_cwnd, self.ax_rtt, self.ax_throughput, self.ax_congestion]:
                ax.set_xlim(x_min, x_max)
                
        return (self.line_cwnd, self.line_rtt, self.line_throughput, self.line_congestion)
    
    def capture_packets(self):
        try:
            print(f"DEBUG: Starting packet capture with:")
            print(f"DEBUG: Interface: {self.interface}")
            print(f"DEBUG: Display filter: {self.display_filter}")
            
            # Find tshark location using the 'which' command
            import subprocess
            try:
                tshark_path = subprocess.check_output(['which', 'tshark']).decode().strip()
                print(f"DEBUG: Found TShark at: {tshark_path}")
            except Exception as e:
                print(f"DEBUG: Couldn't determine TShark path: {e}")
                tshark_path = '/opt/homebrew/bin/tshark'  # Default for macOS Homebrew
                print(f"DEBUG: Using default TShark path: {tshark_path}")
            
            capture = pyshark.LiveCapture(interface=self.interface, display_filter=self.display_filter, tshark_path=tshark_path)
            capture.set_debug()
            print(f"Starting packet capture on interface {self.interface} with filter '{self.display_filter}'...")
            
            for packet in capture.sniff_continuously():
                try:
                    # Update packet count for throughput calculation
                    with self.lock:
                        self.packet_count += 1
                        
                        # Extract TCP window size if available
                        if hasattr(packet.tcp, 'window_size_value'):
                            cwnd = int(packet.tcp.window_size_value)
                            self.latest_cwnd = cwnd
                            
                        # Extract RTT if available
                        if hasattr(packet.tcp, 'analysis_ack_rtt'):
                            rtt = float(packet.tcp.analysis_ack_rtt) * 1000  # Convert to ms
                            self.latest_rtt = rtt
                
                except AttributeError as e:
                    # Some packets may not have all fields
                    print(f"DEBUG: AttributeError - {e}")
                    continue
                except Exception as e:
                    print(f"Error processing packet: {e}")
                    print(f"DEBUG: Packet type: {type(packet)}")
                    continue
                    
        except Exception as e:
            print(f"Error in packet capture: {e}")
            import traceback
            print(f"DEBUG: Full traceback: {traceback.format_exc()}")
    
    def start_capture(self):
        # Start packet capture in a separate thread
        thread = threading.Thread(target=self.capture_packets, daemon=True)
        thread.start()
        return thread
        
    def animate(self, interval=100):  # refresh every 100ms
        """Start the animation with the given refresh interval."""
        # Start packet capture in a background thread
        self.start_capture()
        
        # Create animation that calls update_plot regularly
        ani = FuncAnimation(self.fig, self.update_plot, 
                            interval=interval, 
                            blit=True, 
                            cache_frame_data=False)
        
        # Show the plots
        plt.show()
        
        return ani


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Network Traffic Congestion Visualizer')
    
    parser.add_argument('--interface', type=str, default='lo0',
                        help='Network interface to capture packets from (default: lo0)')
    
    parser.add_argument('--filter', type=str, default='tcp',
                        help='Display filter for packet capture (default: tcp)')
    
    parser.add_argument('--history', type=int, default=100,
                        help='Number of data points to keep in history (default: 100)')
    
    parser.add_argument('--interval', type=int, default=100,
                        help='Refresh interval in milliseconds (default: 100)')
    
    parser.add_argument('--rtt-threshold', type=float, default=100.0,
                        help='RTT threshold in ms for congestion detection (default: 100.0)')
    
    parser.add_argument('--cwnd-threshold', type=float, default=0.7,
                        help='CWND threshold as fraction of max for congestion detection (default: 0.7)')
    
    return parser.parse_args()


if __name__ == "__main__":
    # Parse command line arguments
    args = parse_arguments()
    
    print(f"Starting Network Traffic Congestion Visualizer")
    print(f"Interface: {args.interface}")
    print(f"Display filter: {args.filter}")
    print(f"History length: {args.history} data points")
    print(f"Update interval: {args.interval} ms")
    print(f"RTT congestion threshold: {args.rtt_threshold} ms")
    print(f"CWND congestion threshold: {args.cwnd_threshold} (fraction of max)")
    
    # Create and start the visualizer
    viz = CongestionVisualizer(
        interface=args.interface,
        display_filter=args.filter,
        history_length=args.history,
        congestion_threshold_rtt=args.rtt_threshold,
        congestion_threshold_cwnd=args.cwnd_threshold
    )
    
    # Start the animation
    viz.animate(interval=args.interval)
