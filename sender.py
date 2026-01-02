import json
import time
import requests
import meshtastic
import meshtastic.serial_interface
from constants import Constants
from dto import ApiResponse
from dotenv import load_dotenv
import os


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
    packet_json = json.dumps(packet)
    max_chunk_size = 200  # Adjust based on Meshtastic limits
    chunks = [
        packet_json[i : i + max_chunk_size]
        for i in range(0, len(packet_json), max_chunk_size)
    ]
    total_chunks = len(chunks)

    for idx, chunk in enumerate(chunks):
        message = f"CHUNK:{idx+1}/{total_chunks}:{chunk}"
        iface.sendText(destinationId=Constants.RECEIVER_NODE_ID, text=message)
        print(f"Sent chunk {idx+1}/{total_chunks}: {len(chunk)} bytes")
        time.sleep(0.1)  # Small delay between chunks to avoid overwhelming


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
