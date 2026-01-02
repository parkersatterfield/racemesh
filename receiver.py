import json
import pygame
import time
import meshtastic
import meshtastic.serial_interface

from constants import Constants


# MESHTASTIC CONFIG
print("Connecting to Meshtastic node...")
iface = meshtastic.serial_interface.SerialInterface(
    devPath=Constants.SERIAL_PORT, debugOut=False
)

# Give the node time to sync
time.sleep(2)


# CHUNK HANDLING
chunks = {}  # key: message_id, value: list of chunks


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


def handle_message(packet):
    global race_data, last_rx_time
    try:
        text = packet["decoded"]["text"]
        if text.startswith("CHUNK:"):
            parts = text.split(":", 2)
            if len(parts) == 3:
                chunk_info = parts[1]
                chunk_data = parts[2]
                idx, total = map(int, chunk_info.split("/"))
                message_id = f"{packet['from']}_{packet['id']}"  # unique per message
                if message_id not in chunks:
                    chunks[message_id] = [None] * total
                chunks[message_id][idx - 1] = chunk_data
                if all(c is not None for c in chunks[message_id]):
                    full_message = "".join(chunks[message_id])
                    data = json.loads(full_message)
                    parsed_data = parse_race_data(data)
                    race_data = parsed_data
                    last_rx_time = time.time()
                    print("RX assembled and parsed:", parsed_data)
                    del chunks[message_id]
        else:
            # If not chunked, assume direct JSON
            data = json.loads(text)
            parsed_data = parse_race_data(data)
            race_data = parsed_data
            last_rx_time = time.time()
            print("RX parsed:", parsed_data)
    except Exception as e:
        print("Error handling message:", e)


iface.onReceive = handle_message


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

iface.close()
pygame.quit()
