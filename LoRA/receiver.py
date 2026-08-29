import os
import sys
import time

import pygame
import meshtastic
import meshtastic.serial_interface
from pubsub import pub

from constants import Constants

# =============================================================================
# CONFIGURATION
# =============================================================================
PORT = Constants.SERIAL_PORT if os.name == "nt" else Constants.SERIAL_PORT_LINUX

# Display settings
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 480
FRAME_RATE = 30

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (120, 120, 120)
RED = (255, 80, 80)
GREEN = (80, 255, 80)

# Data age warning threshold (seconds)
DATA_STALE_THRESHOLD = 120


# =============================================================================
# LORA COMMUNICATION
# =============================================================================
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
        """Handle incoming Meshtastic messages and update race data."""
        global race_data, last_rx_time

        decoded = packet.get("decoded", {})
        if "text" not in decoded:
            return  # Skip non-text messages

        text = decoded["text"]
        print("RX text:", text)

        # Initialize race_data if needed
        if race_data is None:
            race_data = self._create_empty_race_data()

        # Process the message and update timestamp if successful
        if self._process_message(text, race_data):
            last_rx_time = time.time()

    def _process_message(self, text, race_data):
        """Process incoming message and update race data. Returns True if timestamp should update."""
        match text:
            case "UPDATE":
                self._handle_update(race_data)
                return False  # UPDATE doesn't update timestamp
            case s if s.startswith("ELAPSED"):
                return self._handle_elapsed(text, race_data)
            case s if s.startswith("POS|"):
                return self._handle_position(text, race_data)
            case s if s.startswith("FASTEST|"):
                return self._handle_fastest(text, race_data)
            case s if s.startswith("LAP|"):
                return self._handle_lap(text, race_data)
            case s if s.startswith("AHEAD|"):
                return self._handle_ahead(text, race_data)
            case s if s.startswith("BEHIND|"):
                return self._handle_behind(text, race_data)
            case s if s.startswith("QUOTE"):
                return self._handle_quote(text, race_data)
            case _:
                return False

    def _handle_update(self, race_data):
        """Handle UPDATE message to clear current race data."""
        self.temp_data = {}
        self.temp_laps = []
        race_data["laps"] = []
        print("Starting new update")

    def _handle_elapsed(self, text, race_data):
        """Handle ELAPSED message."""
        parts = text.split("|")
        if len(parts) >= 2:
            race_data["elapsed"] = parts[1]
            return True
        return False

    def _handle_position(self, text, race_data):
        """Handle POS message."""
        parts = text.split("|")
        if len(parts) >= 3:
            race_data["pos"] = parts[1]
            race_data["best_pos"] = parts[2]
            return True
        return False

    def _handle_fastest(self, text, race_data):
        """Handle FASTEST message."""
        parts = text.split("|")
        if len(parts) >= 3:
            race_data["fastest"] = parts[1]
            race_data["best_lap"] = parts[2]
            return True
        return False

    def _handle_lap(self, text, race_data):
        """Handle LAP message."""
        parts = text.split("|")
        if len(parts) >= 3:
            lap_num = parts[1]
            lap_time_str = parts[2]
            race_data["laps"].append({"num": lap_num, "time": lap_time_str})
            return True
        return False

    def _handle_ahead(self, text, race_data):
        """Handle AHEAD message."""
        parts = text.split("|")
        if len(parts) >= 4:
            race_data["ahead_number"] = parts[1]
            race_data["ahead_name"] = parts[2]
            race_data["ahead_gap"] = parts[3]
            print("AHEAD updated:", race_data["ahead_number"])
            return True
        return False

    def _handle_behind(self, text, race_data):
        """Handle BEHIND message."""
        parts = text.split("|")
        if len(parts) >= 4:
            race_data["behind_number"] = parts[1]
            race_data["behind_name"] = parts[2]
            race_data["behind_gap"] = parts[3]
            print("BEHIND updated:", race_data["behind_number"])
            return True
        return False

    def _handle_quote(self, text, race_data):
        """Handle QUOTE message."""
        race_data["quote"] = text[6:].strip()  # Everything after "QUOTE "
        return False  # Quotes don't update the data timestamp

    @staticmethod
    def _create_empty_race_data():
        """Create an empty race data dictionary with default values."""
        return {
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

    def close(self):
        if self.iface:
            self.iface.close()


# =============================================================================
# DISPLAY INITIALIZATION
# =============================================================================
def setup_sdl_environment():
    """Configure SDL environment variables for headless HDMI output."""
    os.environ["XDG_RUNTIME_DIR"] = "/tmp"
    os.environ["SDL_VIDEODRIVER"] = "kmsdrm"
    os.environ["KMSDRM_DEVICE"] = "/dev/dri/card0"
    os.environ["SDL_VIDEO_KMSDRM_DEVINDEX"] = "0"


def initialize_display():
    """Initialize pygame display and return screen object."""
    setup_sdl_environment()

    print("Configuring display for headless HDMI output...")
    print(f"DRM Device: {os.environ.get('KMSDRM_DEVICE')}")

    try:
        pygame.init()
        print(f"Pygame initialized with driver: {pygame.display.get_driver()}")

        # Try fullscreen first for headless HDMI
        try:
            screen = pygame.display.set_mode(
                (SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN
            )
            print("✓ Fullscreen display created on HDMI")
        except:
            # Fall back to windowed
            screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
            print("✓ Windowed display created")

        pygame.display.set_caption("Race Dashboard")
        return screen

    except Exception as e:
        print(f"ERROR: Could not initialize display: {e}")
        sys.exit(1)


def create_fonts():
    """Create and return font objects."""
    return {
        "xl": pygame.font.SysFont("monospace", 64, bold=True),
        "l": pygame.font.SysFont("monospace", 36),
        "m": pygame.font.SysFont("monospace", 28),
        "s": pygame.font.SysFont("monospace", 22),
        "xs": pygame.font.SysFont("monospace", 16),
    }


# =============================================================================
# RENDERING UTILITIES
# =============================================================================
def wrap_text(text, font, max_width):
    """Wrap text to fit within max_width pixels."""
    words = text.split(" ")
    lines = []
    current_line = []

    for word in words:
        # Try adding the word to current line
        test_line = " ".join(current_line + [word])
        if font.size(test_line)[0] <= max_width:
            current_line.append(word)
        else:
            # Start a new line if current line has words
            if current_line:
                lines.append(" ".join(current_line))
                current_line = [word]
            else:
                # Single word is too long, add it anyway
                lines.append(word)

    # Add remaining words
    if current_line:
        lines.append(" ".join(current_line))

    return lines


def draw_dashboard(screen, fonts, data, age):
    """Render the race dashboard to the screen."""
    y_pos = 10

    # ========== HEADER SECTION ==========
    # Position (big, left)
    screen.blit(fonts["xl"].render(f"P{data['pos']}", True, WHITE), (20, y_pos))
    screen.blit(
        fonts["s"].render(f"(Best: {data.get('best_pos', '-')})", True, GRAY),
        (160, y_pos + 20),
    )
    # Elapsed (right)
    screen.blit(fonts["l"].render(f"{data['elapsed']}", True, WHITE), (500, y_pos + 10))

    y_pos = 100

    # ========== LAPS SECTION ==========
    screen.blit(fonts["s"].render("LAPS", True, GRAY), (20, y_pos))
    y_pos += 35

    # Fastest lap
    screen.blit(
        fonts["l"].render(
            f"FASTEST {data['fastest']} (L{data.get('best_lap', '-')})", True, WHITE
        ),
        (20, y_pos),
    )
    y_pos += 50

    # Last 3 laps in descending order (newest first)
    laps = data["laps"][-3:]  # Get last 3 laps
    laps.reverse()
    best_lap_num = data.get("best_lap", "-")
    for lap in laps:
        lap_color = GREEN if lap["num"] == best_lap_num else WHITE
        screen.blit(
            fonts["m"].render(f"L{lap['num']}: {lap['time']}", True, lap_color),
            (20, y_pos),
        )
        y_pos += 35

    y_pos = 320

    # ========== GAPS SECTION ==========
    screen.blit(fonts["s"].render("GAPS", True, GRAY), (20, y_pos))
    y_pos += 35

    # Car ahead
    ahead_num = data.get("ahead_number", "-")
    ahead_name = data.get("ahead_name", "-")
    ahead_gap = data.get("ahead_gap", "-")
    if ahead_num != "NONE":
        # Display label and car info in white
        screen.blit(
            fonts["m"].render(f"AHEAD: #{ahead_num} {ahead_name} +", True, WHITE),
            (20, y_pos),
        )
        # Display gap time in green
        gap_x_offset = fonts["m"].size(f"AHEAD: #{ahead_num} {ahead_name} +")[0]
        screen.blit(
            fonts["m"].render(f"{ahead_gap}", True, GREEN),
            (20 + gap_x_offset, y_pos),
        )
    else:
        screen.blit(fonts["m"].render(f"AHEAD: Leading!", True, WHITE), (20, y_pos))
    y_pos += 40

    # Car behind
    behind_num = data.get("behind_number", "-")
    behind_name = data.get("behind_name", "-")
    behind_gap = data.get("behind_gap", "-")
    if behind_num != "NONE":
        screen.blit(
            fonts["m"].render(f"BEHIND: #{behind_num} {behind_name} -", True, WHITE),
            (20, y_pos),
        )
        # Display gap time in red
        gap_x_offset = fonts["m"].size(f"BEHIND: #{behind_num} {behind_name} -")[0]
        screen.blit(
            fonts["m"].render(f"{behind_gap}", True, RED),
            (20 + gap_x_offset, y_pos),
        )
    else:
        screen.blit(fonts["m"].render(f"BEHIND: Last", True, WHITE), (20, y_pos))
    y_pos += 50

    # ========== MOTIVATION SECTION ==========
    quote = data.get("quote", None)
    if quote:
        screen.blit(fonts["s"].render("MOTIVATION", True, GRAY), (20, y_pos))
        y_pos += 35
        # Wrap the quote text to fit screen width (760 pixels for padding)
        wrapped_lines = wrap_text(quote, fonts["s"], 760)
        for line in wrapped_lines[:2]:  # Limit to 2 lines to avoid overflow
            screen.blit(fonts["s"].render(line, True, WHITE), (20, y_pos))
            y_pos += 25

    # Update age
    y_pos += 40
    color = GRAY if age < DATA_STALE_THRESHOLD else RED
    screen.blit(
        fonts["xs"].render(f"Updated {int(age)}s ago", True, color), (20, y_pos)
    )


# =============================================================================
# MAIN APPLICATION
# =============================================================================
def main():
    """Main application loop."""
    global race_data, last_rx_time

    # Initialize display and fonts
    screen = initialize_display()
    fonts = create_fonts()
    clock = pygame.time.Clock()

    # Initialize LoRa listener
    listener = LoRaListener(PORT)
    listener_connected = False

    # Global state
    race_data = None
    last_rx_time = None

    running = True
    frame_count = 0

    try:
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

            # Render dashboard or waiting message
            screen.fill(BLACK)
            if race_data and last_rx_time:
                age = time.time() - last_rx_time
                draw_dashboard(screen, fonts, race_data, age)
            else:
                msg = (
                    "Connecting to LoRa..."
                    if not listener_connected
                    else "Waiting for race data..."
                )
                screen.blit(fonts["l"].render(msg, True, WHITE), (20, 20))

            pygame.display.update()
            clock.tick(FRAME_RATE)
            frame_count += 1

    finally:
        listener.close()
        pygame.quit()


if __name__ == "__main__":
    print(f"Using serial port: {PORT}")
    main()
