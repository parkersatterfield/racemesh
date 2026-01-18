import json
import pygame
import time
import meshtastic
import meshtastic.serial_interface
import os
import sys
from pubsub import pub

from constants import Constants

# Set SDL environment variables BEFORE pygame.init()
os.environ["XDG_RUNTIME_DIR"] = "/tmp"

# Configure for headless system with HDMI display
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["KMSDRM_DEVICE"] = "/dev/dri/card0"  # Explicitly use card0 for diet pi
# Try to force fullscreen mode on the HDMI output
os.environ["SDL_VIDEO_KMSDRM_DEVINDEX"] = "0"  # Use first DRM device

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

        # Initialize race_data if it doesn't exist
        if race_data is None:
            race_data = {
                "pos": "-",
                "best_pos": "-",
                "elapsed": "-",
                "fastest": "-",
                "best_lap": "-",
                "laps": [],
                "ahead_number": "-",
                "ahead_name": "-",
                "ahead_gap": "-",
                "behind_number": "-",
                "behind_name": "-",
                "behind_gap": "-",
            }

        match text:
            case "UPDATE":
                self.temp_data = {}
                self.temp_laps = []
                race_data["laps"] = []
                print("Starting new update")
            case s if s.startswith("ELAPSED"):
                parts = text.split("|")
                race_data["elapsed"] = parts[1]
                last_rx_time = time.time()
            case s if s.startswith("POS|"):
                parts = text.split("|")
                if len(parts) >= 3:
                    race_data["pos"] = parts[1]
                    race_data["best_pos"] = parts[2]
                    last_rx_time = time.time()
            case s if s.startswith("FASTEST|"):
                parts = text.split("|")
                if len(parts) >= 3:
                    race_data["fastest"] = parts[1]
                    race_data["best_lap"] = parts[2]
                    last_rx_time = time.time()
            case s if s.startswith("LAP|"):
                parts = text.split("|")
                if len(parts) >= 3:
                    lap_num = parts[1]
                    lap_time_str = parts[2]
                    race_data["laps"].append({"num": lap_num, "time": lap_time_str})
                    last_rx_time = time.time()
            case s if s.startswith("AHEAD|"):
                parts = text.split("|")
                if len(parts) >= 4:
                    race_data["ahead_number"] = parts[1]
                    race_data["ahead_name"] = parts[2]
                    race_data["ahead_gap"] = parts[3]
                    last_rx_time = time.time()
                    print("AHEAD updated:", race_data["ahead_number"])
            case s if s.startswith("BEHIND|"):
                parts = text.split("|")
                if len(parts) >= 4:
                    race_data["behind_number"] = parts[1]
                    race_data["behind_name"] = parts[2]
                    race_data["behind_gap"] = parts[3]
                    last_rx_time = time.time()
                    print("BEHIND updated:", race_data["behind_number"])

    def close(self):
        if self.iface:
            self.iface.close()


# Global state
race_data = None
last_rx_time = None
last_message = "Waiting for messages..."


# Set SDL environment variables BEFORE pygame.init()
os.environ["XDG_RUNTIME_DIR"] = "/tmp"

# Configure for headless system with HDMI display
os.environ["SDL_VIDEODRIVER"] = "kmsdrm"
os.environ["KMSDRM_DEVICE"] = "/dev/dri/card0"  # Explicitly use card0 for diet pi
# Try to force fullscreen mode on the HDMI output
os.environ["SDL_VIDEO_KMSDRM_DEVINDEX"] = "0"  # Use first DRM device

print("Configuring display for headless HDMI output...")
print(f"DRM Device: {os.environ.get('KMSDRM_DEVICE')}")

try:
    pygame.init()
    print(f"Pygame initialized with driver: {pygame.display.get_driver()}")

    # Try fullscreen first for headless HDMI
    try:
        screen = pygame.display.set_mode((800, 480), pygame.FULLSCREEN)
        print("✓ Fullscreen display created on HDMI")
    except:
        # Fall back to windowed
        screen = pygame.display.set_mode((800, 480))
        print("✓ Windowed display created")

    pygame.display.set_caption("Race Dashboard")

except Exception as e:
    print(f"ERROR: Could not initialize display: {e}")
    sys.exit(1)

clock = pygame.time.Clock()

FONT_XL = pygame.font.SysFont("monospace", 64, bold=True)
FONT_L = pygame.font.SysFont("monospace", 36)
FONT_M = pygame.font.SysFont("monospace", 28)
FONT_S = pygame.font.SysFont("monospace", 22)
FONT_XS = pygame.font.SysFont("monospace", 16)

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (120, 120, 120)
RED = (255, 80, 80)
GREEN = (80, 255, 80)


# Create LoRa listener (will connect in main loop)
listener = LoRaListener(PORT)
listener_connected = False


# DRAW DASHBOARD
def draw_dashboard(data, age):
    y_pos = 10

    # ========== HEADER SECTION ==========
    # Position (big, left)
    screen.blit(FONT_XL.render(f"P{data['pos']}", True, WHITE), (20, y_pos))
    screen.blit(
        FONT_S.render(f"(Best: {data.get('best_pos', '-')})", True, GRAY),
        (160, y_pos + 20),
    )
    # Elapsed (right)
    screen.blit(FONT_L.render(f"{data['elapsed']}", True, WHITE), (500, y_pos + 10))

    y_pos = 100

    # ========== LAPS SECTION ==========
    screen.blit(FONT_S.render("LAPS", True, GRAY), (20, y_pos))
    y_pos += 35

    # Fastest lap
    screen.blit(
        FONT_L.render(
            f"FASTEST {data['fastest']} (L{data.get('best_lap', '-')})", True, WHITE
        ),
        (20, y_pos),
    )
    y_pos += 50

    # Last 3 laps in descending order (newest first)
    laps = data["laps"][-3:]  # Get last 3 laps
    laps.reverse()  # Reverse to show in descending order (16, 15, 14)
    best_lap_num = data.get("best_lap", "-")
    for lap in laps:
        # Color green if this is the fastest lap
        lap_color = GREEN if lap["num"] == best_lap_num else WHITE
        screen.blit(
            FONT_M.render(f"L{lap['num']}: {lap['time']}", True, lap_color),
            (20, y_pos),
        )
        y_pos += 35

    y_pos = 320

    # ========== GAPS SECTION ==========
    screen.blit(FONT_S.render("GAPS", True, GRAY), (20, y_pos))
    y_pos += 35

    # Car ahead
    ahead_num = data.get("ahead_number", "-")
    ahead_name = data.get("ahead_name", "-")
    ahead_gap = data.get("ahead_gap", "-")
    if ahead_num != "NONE":
        # Display label and car info in white
        screen.blit(
            FONT_M.render(f"AHEAD: #{ahead_num} {ahead_name} +", True, WHITE),
            (20, y_pos),
        )
        # Display gap time in green
        gap_x_offset = FONT_M.size(f"AHEAD: #{ahead_num} {ahead_name} +")[0]
        screen.blit(
            FONT_M.render(f"{ahead_gap}", True, GREEN),
            (20 + gap_x_offset, y_pos),
        )
    else:
        screen.blit(FONT_M.render(f"AHEAD: Leading!", True, WHITE), (20, y_pos))
    y_pos += 40

    # Car behind
    behind_num = data.get("behind_number", "-")
    behind_name = data.get("behind_name", "-")
    behind_gap = data.get("behind_gap", "-")
    if behind_num != "NONE":
        # Display label and car info in white
        screen.blit(
            FONT_M.render(f"BEHIND: #{behind_num} {behind_name} -", True, WHITE),
            (20, y_pos),
        )
        # Display gap time in red
        gap_x_offset = FONT_M.size(f"BEHIND: #{behind_num} {behind_name} -")[0]
        screen.blit(
            FONT_M.render(f"{behind_gap}", True, RED),
            (20 + gap_x_offset, y_pos),
        )
    else:
        screen.blit(FONT_M.render(f"BEHIND: Last", True, WHITE), (20, y_pos))

    # Update age
    color = GRAY if age < 120 else RED
    screen.blit(FONT_XS.render(f"Updated {int(age)}s ago", True, color), (20, 450))

    pygame.display.flip()


# MAIN LOOP
running = True
frame_count = 0

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Connect to listener on first frame after display is shown
    if not listener_connected and frame_count == 1:
        try:
            listener.connect()
            listener_connected = True
        except Exception as e:
            print(f"Failed to connect to LoRa: {e}")

    if race_data and last_rx_time:
        screen.fill(BLACK)
        age = time.time() - last_rx_time
        draw_dashboard(race_data, age)
        pygame.display.update()
    else:
        screen.fill(BLACK)
        msg = (
            "Connecting to LoRa..."
            if not listener_connected
            else "Waiting for race data..."
        )
        screen.blit(FONT_L.render(msg, True, WHITE), (20, 20))
        pygame.display.update()

    # Always show last message
    # screen.blit(FONT_S.render(last_message[:50], True, GRAY), (20, 440))

    clock.tick(30)
    frame_count += 1

listener.close()
pygame.quit()
