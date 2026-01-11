import json
import pygame
import time
import meshtastic
import meshtastic.serial_interface
import os
import sys
from pubsub import pub

from constants import Constants

PORT = Constants.SERIAL_PORT if os.name == "nt" else Constants.SERIAL_PORT_LINUX
print(PORT)


class LoRaListener:
    def __init__(self, serial_port):
        self.serial_port = serial_port
        self.iface = None
        self.temp_data = {}
        self.temp_laps = []

    def connect(self):
        print("Connecting to Meshtastic node...")
        self.iface = meshtastic.serial_interface.SerialInterface(
            devPath=self.serial_port, debugOut=False
        )
        time.sleep(2)  # Give the node time to sync
        print("Connected.")
        print("Listening for messages...")
        pub.subscribe(self.handle_message, "meshtastic.receive")

    def handle_message(self, packet, interface):
        global last_message, race_data, last_rx_time

        decoded = packet.get("decoded", {})
        if "text" not in decoded:
            return  # Skip non-text messages
        text = decoded["text"]
        print("RX text:", text)

        match text:
            case "UPDATE":
                self.temp_data = {}
                self.temp_laps = []
                print("Starting new update")
            case s if s.startswith("POS:"):
                self.temp_data["pos"] = text.split(":", 1)[1]
            case s if s.startswith("ELAPSED:"):
                self.temp_data["elapsed"] = parse_time(text.split(":", 1)[1])
            case s if s.startswith("FASTEST:"):
                self.temp_data["fastest"] = parse_time(text.split(":", 1)[1])
            case s if s.startswith("LAP|"):
                parts = text.split("|")
                if len(parts) >= 3:
                    lap_num = parts[1]
                    lap_time_str = parts[2]
                    self.temp_laps.append({"num": lap_num, "time": lap_time_str})

        # Check if we have all data to update (at least pos, elapsed, fastest, and some laps)
        if (
            "pos" in self.temp_data
            and "elapsed" in self.temp_data
            and "fastest" in self.temp_data
            and len(self.temp_laps) > 0
        ):
            race_data = {
                "pos": self.temp_data["pos"],
                "elapsed": self.temp_data["elapsed"],
                "fastest": self.temp_data["fastest"],
                "laps": self.temp_laps,
            }
            last_rx_time = time.time()
            print("Race data updated:", race_data)
            last_message = "Race data updated"

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


# Global state
race_data = None
last_rx_time = None
last_message = "Waiting for messages..."


# Initialize LoRa listener
listener = LoRaListener(PORT)
listener.connect()


def check_display_connected():
    """Check if a display is connected by inspecting /sys/class/drm/."""
    drm_path = "/sys/class/drm/"
    if not os.path.exists(drm_path):
        # Not on Linux or DRM not available, assume connected
        return True
    try:
        for item in os.listdir(drm_path):
            status_file = os.path.join(drm_path, item, "status")
            if os.path.exists(status_file):
                with open(status_file, "r") as f:
                    status = f.read().strip()
                    if status == "connected":
                        return True
        return False
    except (OSError, IOError):
        # If we can't read, assume connected to avoid blocking
        return True

    # if not check_display_connected():
    print(
        "Error: No connected display detected. Please connect a display and try again."
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

    # Position (big, top-left)
    screen.blit(FONT_XL.render(f"P{data['pos']}", True, WHITE), (20, 20))

    # Elapsed (top-right)
    elapsed = int(data["elapsed"])
    screen.blit(
        FONT_L.render(f"ELAPSED {elapsed//60}:{elapsed%60:02d}", True, WHITE), (480, 30)
    )

    # Gaps TODO
    # screen.blit(FONT_L.render(f"AHEAD +{data['ahead']:.2f}", True, WHITE), (20, 130))
    # screen.blit(FONT_L.render(f"BEHIND +{data['behind']:.2f}", True, WHITE), (20, 180))

    # Fastest lap
    screen.blit(FONT_L.render(f"FAST {data['fastest']:.3f}", True, WHITE), (20, 250))

    # Last 3 laps
    for i, lap in enumerate(data["laps"][-3:]):
        screen.blit(
            FONT_M.render(f"L{lap['num']}: {lap['time']}", True, WHITE),
            (480, 140 + i * 40),
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

    screen.fill(BLACK)

    if race_data:
        age = time.time() - last_rx_time
        draw_dashboard(race_data, age)
    else:
        screen.blit(FONT_L.render("Waiting for race data...", True, WHITE), (20, 20))

    # Always show last message
    screen.blit(FONT_S.render(last_message[:50], True, GRAY), (20, 440))

    pygame.display.flip()

    clock.tick(10)

listener.close()
pygame.quit()
