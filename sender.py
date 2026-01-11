import json
import time
import requests
import meshtastic
import meshtastic.serial_interface
from constants import Constants
from dto import ApiResponse
from dotenv import load_dotenv
import os
import uuid


# CONFIG
load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")
URL = (
    Constants.API_URL
    + f"racerId={Constants.RACER_ID}&raceId={Constants.RACE_ID}&apiToken={API_TOKEN}"
)
print(URL)


# LORA
print("Connecting to Meshtastic node...")
iface = meshtastic.serial_interface.SerialInterface(
    devPath=Constants.SERIAL_PORT, debugOut=False
)

# Give the node time to sync
time.sleep(2)


# FETCH + FORMAT
def fetch_race_data():
    """
    Fetch race data from API and return the full response as DTO.
    """
    r = requests.get(URL)
    r.raise_for_status()
    response = r.json()

    # Parse response into DTO
    api_response = ApiResponse(**response)
    if not api_response.Successful:
        raise ValueError("API response indicates failure")
    return api_response.model_dump()


# MOCK RESPONSE FOR TESTING
def mock_fetch_race_data():
    """
    Return a mock race data response for testing.
    """
    with open("example_response.json") as f:
        data = json.load(f)
    api_response = ApiResponse(**data)
    return api_response.model_dump()


# SEND
def send_packet(packet):
    SERIAL_DELAY = 2.5  # seconds

    competitor = packet["Details"]["Competitor"]
    laps = packet["Details"]["Laps"]
    print(f"Sending data for competitor: {competitor.get('RacerName', 'Unknown')}")
    # Send update start
    iface.sendText(destinationId=Constants.RECEIVER_NODE_ID, text="UPDATE")
    time.sleep(SERIAL_DELAY)

    # Send position
    pos = competitor.get("Position", "0")
    print(f"position: {pos}")
    iface.sendText(destinationId=Constants.RECEIVER_NODE_ID, text=f"POS:{pos}")
    time.sleep(SERIAL_DELAY)

    # Send elapsed time
    elapsed = competitor.get("TotalTime", "0")
    print(f"elapsed time: {elapsed}")
    iface.sendText(destinationId=Constants.RECEIVER_NODE_ID, text=f"ELAPSED:{elapsed}")
    time.sleep(SERIAL_DELAY)

    # Send fastest lap
    fastest = competitor.get("BestLapTime", "0")
    print(f"best lap: {fastest}")
    iface.sendText(destinationId=Constants.RECEIVER_NODE_ID, text=f"FASTEST:{fastest}")
    time.sleep(SERIAL_DELAY)

    # Send laps — sort by lap number and send last 3
    try:
        sorted_laps = sorted(laps, key=lambda l: int(l.get("Lap", 0)))
    except Exception:
        sorted_laps = laps

    for lap in sorted_laps[-3:]:
        lap_time = lap.get("LapTime", "0")
        lap_num = lap.get("Lap", "1")
        print(f"lap {lap_num}: {lap_time}")
        iface.sendText(
            destinationId=Constants.RECEIVER_NODE_ID, text=f"LAP:{lap_num}:{lap_time}"
        )
        time.sleep(SERIAL_DELAY)


# MAIN LOOP
print("Race sender started")

while True:
    try:
        # race_data = fetch_race_data() # TODO uncomment for live
        race_data = mock_fetch_race_data()
        send_packet(race_data)
    except Exception as e:
        print("ERROR fetching or sending data:", e)

    time.sleep(60)
