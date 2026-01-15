import json
import time
import requests
import meshtastic
import meshtastic.serial_interface
from constants import Constants
from dto import ApiResponse, SessionResponse
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
SESSION_URL = Constants.API_URL + f"raceId={Constants.RACE_ID}&apiToken={API_TOKEN}"
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
    r = requests.post(URL)
    r.raise_for_status()
    response = r.json()

    # Parse response into DTO
    api_response = ApiResponse(**response)
    if not api_response.Successful:
        raise ValueError("API response indicates failure")
    return api_response.model_dump()


def fetch_session_data():
    """
    Fetch session data from API, filter by class, and return car ahead and behind.
    """
    r = requests.post(SESSION_URL)
    r.raise_for_status()
    response = r.json()

    # Parse response into DTO
    api_response = SessionResponse(**response)
    if not api_response.Successful:
        raise ValueError("API response indicates failure")

    session = api_response.Session
    competitors = session.Competitors

    # Find my competitor data
    my_competitor = None
    for comp_id, comp in competitors.items():
        if comp.RacerID == str(Constants.RACER_ID) or comp.Number == str(
            Constants.RACER_ID
        ):
            my_competitor = comp
            break

    if not my_competitor:
        raise ValueError(f"Racer {Constants.RACER_ID} not found in session data")

    my_class_id = my_competitor.ClassID

    # Filter competitors by my class and sort by position
    class_competitors = [
        comp
        for comp in competitors.values()
        if comp.ClassID == my_class_id and comp.Position
    ]

    # Sort by position (convert to int for proper sorting)
    class_competitors.sort(
        key=lambda c: int(c.Position) if c.Position.isdigit() else 999
    )

    # Find my position in the sorted list
    my_position_index = next(
        (
            i
            for i, comp in enumerate(class_competitors)
            if comp.RacerID == my_competitor.RacerID
        ),
        None,
    )

    car_ahead = None
    car_behind = None

    if my_position_index is not None:
        # Car ahead is the one before me in the list (lower index = better position)
        if my_position_index > 0:
            car_ahead = class_competitors[my_position_index - 1]

        # Car behind is the one after me in the list
        if my_position_index < len(class_competitors) - 1:
            car_behind = class_competitors[my_position_index + 1]

    return {
        "my_competitor": my_competitor.model_dump(),
        "car_ahead": car_ahead.model_dump() if car_ahead else None,
        "car_behind": car_behind.model_dump() if car_behind else None,
        "my_position": my_competitor.Position,
        "total_in_class": len(class_competitors),
    }


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
    print(
        f"Sending data for competitor: {competitor.get('LastName', 'Unknown')}, {competitor.get('FirstName', 'Unknown')}"
    )
    # Send update start
    iface.sendText(destinationId=Constants.RECEIVER_NODE_ID, text="UPDATE")
    time.sleep(SERIAL_DELAY)

    # Send position and best position
    pos = competitor.get("Position", "0")
    best_pos = competitor.get("BestPosition", "0")
    print(f"position: {pos}, best position: {best_pos}")
    iface.sendText(
        destinationId=Constants.RECEIVER_NODE_ID, text=f"POS|{pos}|{best_pos}"
    )
    time.sleep(SERIAL_DELAY)

    # Send elapsed time
    elapsed = competitor.get("TotalTime", "0")
    print(f"elapsed time: {elapsed}")
    iface.sendText(destinationId=Constants.RECEIVER_NODE_ID, text=f"ELAPSED|{elapsed}")
    time.sleep(SERIAL_DELAY)

    # Send fastest lap and best lap number
    fastest = competitor.get("BestLapTime", "0")
    best_lap = competitor.get("BestLap", "0")
    print(f"best lap: {fastest} (Lap {best_lap})")
    iface.sendText(
        destinationId=Constants.RECEIVER_NODE_ID, text=f"FASTEST|{fastest}|{best_lap}"
    )
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
            destinationId=Constants.RECEIVER_NODE_ID, text=f"LAP|{lap_num}|{lap_time}"
        )
        time.sleep(SERIAL_DELAY)


def send_position_packet(position_data):
    """
    Send position data (car ahead and behind) to receiver.
    """
    SERIAL_DELAY = 2.5  # seconds

    my_pos = position_data.get("my_position", "?")
    total = position_data.get("total_in_class", "?")
    car_ahead = position_data.get("car_ahead")
    car_behind = position_data.get("car_behind")

    print(f"Position in class: {my_pos}/{total}")

    # Send car ahead info
    if car_ahead:
        ahead_name = f"{car_ahead['FirstName']} {car_ahead['LastName']}"
        ahead_number = car_ahead["Number"]
        ahead_gap = car_ahead.get("TotalTime", "00:00:00.000")
        print(f"Car ahead: #{ahead_number} {ahead_name}")
        iface.sendText(
            destinationId=Constants.RECEIVER_NODE_ID,
            text=f"AHEAD|{ahead_number}|{ahead_name}|{ahead_gap}",
        )
    else:
        print("No car ahead (leading the class)")
        iface.sendText(
            destinationId=Constants.RECEIVER_NODE_ID,
            text="AHEAD|NONE|Leading|00:00:00.000",
        )

    time.sleep(SERIAL_DELAY)

    # Send car behind info
    if car_behind:
        behind_name = f"{car_behind['FirstName']} {car_behind['LastName']}"
        behind_number = car_behind["Number"]
        behind_gap = car_behind.get("TotalTime", "00:00:00.000")
        print(f"Car behind: #{behind_number} {behind_name}")
        iface.sendText(
            destinationId=Constants.RECEIVER_NODE_ID,
            text=f"BEHIND|{behind_number}|{behind_name}|{behind_gap}",
        )
    else:
        print("No car behind (last in class)")
        iface.sendText(
            destinationId=Constants.RECEIVER_NODE_ID,
            text="BEHIND|NONE|Last|00:00:00.000",
        )

    time.sleep(SERIAL_DELAY)


# MAIN LOOP
print("Race sender started")

while True:
    try:
        # race_data = mock_fetch_race_data()
        race_data = fetch_race_data()  # TODO uncomment for live
        send_packet(race_data)

        session_data = fetch_session_data()
        send_position_packet(session_data)
    except Exception as e:
        print("ERROR fetching or sending data:", e)

    time.sleep(15)
