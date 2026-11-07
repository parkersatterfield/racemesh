import meshtastic
import meshtastic.serial_interface
import time

from constants import Constants

PORT = "COM3"


def main():
    print("Connecting to Meshtastic node...")
    iface = meshtastic.serial_interface.SerialInterface(devPath=PORT, debugOut=False)

    # Give the node time to sync
    time.sleep(2)

    message = "Hello from Python via Meshtastic!"
    iface.sendText(destinationId=Constants.RECEIVER_NODE_ID, text=message)

    print("Message sent!")

    # Clean shutdown
    iface.close()


if __name__ == "__main__":
    main()
