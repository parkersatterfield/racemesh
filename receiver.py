import json
import pygame
import time
import meshtastic
import meshtastic.serial_interface
import subprocess
import sys

from constants import Constants


class LoRaListener:
    def __init__(self, serial_port, on_message_callback):
        self.serial_port = serial_port
        self.on_message_callback = on_message_callback
        self.iface = None
        self.chunks = {}  # key: message_id, value: list of chunks

    def connect(self):
        print("Connecting to Meshtastic node...")
        self.iface = meshtastic.serial_interface.SerialInterface(
            devPath=self.serial_port, debugOut=False
        )
        time.sleep(2)  # Give the node time to sync
        self.iface.onReceive = self.handle_message

    def handle_message(self, packet):
        try:
            text = packet["decoded"]["text"]
            if text.startswith("CHUNK:"):
                parts = text.split(":", 2)

                if len(parts) == 3:
                    chunk_info = parts[1]
                    chunk_data = parts[2]
                    idx, total = map(int, chunk_info.split("/"))
                    message_id = (
                        f"{packet['from']}_{packet['id']}"  # unique per message
                    )

                    if message_id not in self.chunks:
                        self.chunks[message_id] = [None] * total
                    self.chunks[message_id][idx - 1] = chunk_data

                    if all(c is not None for c in self.chunks[message_id]):
                        full_message = "".join(self.chunks[message_id])
                        data = json.loads(full_message)
                        self.on_message_callback(data)
                        print("RX assembled and parsed:", data)
                        del self.chunks[message_id]
            else:
                # If not chunked, assume direct JSON
                data = json.loads(text)
                self.on_message_callback(data)
                print("RX parsed:", data)

        except Exception as e:
            print("Error handling message:", e)

    def close(self):
        if self.iface:
            self.iface.close()


def parse_time(time_str):
    """Parse time string like '1:23.456' to seconds as float."""
    if not time_str or time_str == "string":
        return 0.0
    try:
        if ":" in time_str:
            minutes, seconds = time_str.split(":")
            return int(minutes) * 60 + float(seconds)
        else:
            return float(time_str)
    except ValueError:
        return 0.0


def parse_race_data(data):
    """Parse the received JSON data into the format expected by draw_dashboard."""
    competitor = data.get("Details", {}).get("Competitor", {})
    laps_data = data.get("Details", {}).get("Laps", [])

    return {
        "pos": competitor.get("Position", "0"),
        "elapsed": parse_time(competitor.get("TotalTime", "0")),
        "fastest": parse_time(competitor.get("BestLapTime", "0")),
        "laps": [parse_time(lap.get("LapTime", "0")) for lap in laps_data],
    }


# Global state
race_data = None
last_rx_time = None


def update_inputs(message_body):
    global race_data, last_rx_time
    parsed_data = parse_race_data(message_body)
    race_data = parsed_data
    last_rx_time = time.time()


# Initialize LoRa listener
listener = LoRaListener(Constants.SERIAL_PORT_LINUX, update_inputs)
listener.connect()


def check_display_connected():
    """Check if an HDMI or any display is connected using xrandr."""
    try:
        result = subprocess.run(["xrandr"], capture_output=True, text=True)
        if result.returncode == 0:
            # Parse output for connected displays
            lines = result.stdout.split("\n")
            for line in lines:
                if " connected" in line and (
                    "HDMI" in line or "DP" in line or "VGA" in line or "DVI" in line
                ):
                    return True
        return False
    except FileNotFoundError:
        # xrandr not available, assume display is connected or handle differently
        return True  # For Windows or other systems


if not check_display_connected():
    print(
        "Error: No connected display detected. Please connect an HDMI display and try again."
    )
    sys.exit(1)


# DISPLAY CONFIG
pygame.init()
screen = pygame.display.set_mode((800, 480))
pygame.display.set_caption("Race Dashboard")
clock = pygame.time.Clock()

FONT_XL = pygame.font.SysFont("monospace", 64, bold=True)
FONT_L = pygame.font.SysFont("monospace", 36)
FONT_M = pygame.font.SysFont("monospace", 28)
FONT_S = pygame.font.SysFont("monospace", 22)

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (120, 120, 120)
RED = (255, 80, 80)


# STATE
race_data = None
last_rx_time = None


# DRAW DASHBOARD
def draw_dashboard(data, age):
    screen.fill(BLACK)

    # Position (big, top-left)
    screen.blit(FONT_XL.render(f"P{data['pos']}", True, WHITE), (20, 20))

    # Elapsed (top-right)
    elapsed = int(data["elapsed"])
    screen.blit(
        FONT_L.render(f"ELAPSED {elapsed//60}:{elapsed%60:02d}", True, WHITE), (480, 30)
    )

    # Gaps
    screen.blit(FONT_L.render(f"AHEAD +{data['ahead']:.2f}", True, WHITE), (20, 130))
    screen.blit(FONT_L.render(f"BEHIND +{data['behind']:.2f}", True, WHITE), (20, 180))

    # Fastest lap
    screen.blit(FONT_L.render(f"FAST {data['fastest']:.3f}", True, WHITE), (20, 250))

    # Last 3 laps
    for i, lap in enumerate(data["laps"][-3:]):
        screen.blit(
            FONT_M.render(f"L{i+1}: {lap:.3f}", True, WHITE), (480, 140 + i * 40)
        )

    # Update age
    color = WHITE if age < 90 else RED
    screen.blit(FONT_S.render(f"UPDATED {int(age)}s AGO", True, color), (20, 420))

    pygame.display.flip()


# MAIN LOOP
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Draw if we have data
    if race_data:
        age = time.time() - last_rx_time
        draw_dashboard(race_data, age)

    clock.tick(10)

listener.close()
pygame.quit()
