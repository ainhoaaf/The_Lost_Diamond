# Twins

They simulate the boards against the same broker. Mosquitto and the controller (`python3 -m lost_diamond.main` from `server/`) must be running.

- `meeple.py`: joins with a MAC, compares `current_mac`, publishes a cell or a UID when you type it, and prints its own cell when the controller moves it.
- `station.py`: Enter is the button. The terminal prints the screen and the buzzer.
- `play.py`: opens the four meeples and the station, each in its own window.

A single one:

```bash
python3 meeple.py --broker 127.0.0.1 --mac AA:BB:CC:DD:EE:01
python3 station.py --broker 127.0.0.1
```
