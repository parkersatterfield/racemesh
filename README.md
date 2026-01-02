# RaceMesh 🏁

**Real-time race telemetry over LoRa for the 24 Hours of Lemons endurance racing series!**

RaceMesh bridges the gap between the paddock's WiFi-connected computers and the high-speed chaos of the track. Send live race data from the pits to your car's dashboard using Meshtastic-powered LoRa communication, keeping drivers informed without relying on spotty cellular signals or expensive telemetry systems.


## 🚀 Features

- **Wireless Telemetry**: Fetch real-time race data from the Race-Monitor API and transmit it over LoRa using Meshtastic firmware.
- **Chunked Messaging**: Handles large payloads by splitting data into manageable chunks for reliable transmission.
- **Live Dashboard**: Display position, elapsed time, fastest laps, and recent lap times on a Pygame-powered in-car screen.
- **Robust Parsing**: Automatically parses API responses into display-ready formats.
- **Endurance Ready**: Designed for 24-hour races with minimal power consumption and reliable long-range communication.

## 🛠️ Hardware Requirements

- **Sender Setup** (Paddock):
  - Computer with WiFi (e.g., laptop or Raspberry Pi).
  - Heltec v3 LoRa module with Meshtastic firmware.

- **Receiver Setup** (In-Car):
  - Raspberry Pi (or similar) with display (800x480 resolution recommended).
  - Heltec v3 LoRa module with Meshtastic firmware.
  - Optional: Touchscreen for future interactivity.

## 🚗 Usage

### Sender (Paddock)
Run the sender to fetch and transmit race data every 60 seconds:
```bash
uv run sender.py
```
- Fetches data from the API (or uses mock data for testing).
- Sends chunked messages to the receiver node.

### Receiver (In-Car)
Run the receiver to listen for messages and display the dashboard:
```bash
uv run receiver.py
```
- Receives and reassembles chunked data.
- Displays live race info on the screen.

### Testing
- Use `mock_fetch_race_data()` in `sender.py` for offline testing.
- Monitor console output for sent/received messages.

## 📊 Data Flow

1. **Sender**: API → Parse → Chunk → LoRa Transmit
2. **Receiver**: LoRa Receive → Reassemble → Parse → Display

Payloads are JSON-based, with automatic chunking for sizes >200 bytes.

## 🐛 Troubleshooting

- **No Messages Received?** Check node IDs, serial ports, and Meshtastic device pairing.
- **Display Issues?** Ensure Pygame is installed and the Pi has a compatible screen.
- **API Errors?** Verify your API token and racer/race IDs.
- **Chunking Problems?** Adjust `max_chunk_size` in `sender.py` based on your LoRa settings.

## 🤝 Contributing

Contributions welcome! Fork the repo, make changes, and submit a PR. Ideas:
- Add gap calculations (ahead/behind).
- Implement touchscreen controls.
- Optimize for battery-powered receivers.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🏎️ About 24 Hours of Lemons

[24 Hours of Lemons](https://24hoursoflemons.com/) is a hilarious, low-budget endurance racing series where teams build cars from junkyard parts. RaceMesh keeps you in the loop without the luxury of modern telemetry!

---

**Gear up, pit crew! May your packets be strong and your laps be fast. 🏁**</content>
<parameter name="filePath">c:\Users\Parker\Repos\racemesh\README.md
