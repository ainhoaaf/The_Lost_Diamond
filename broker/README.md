# Broker

Mosquitto runs on the PC. The twins and the boards connect here. On this Mac it is installed with Homebrew, and the installer asks for the password.

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install mosquitto
cd "/Users/university/Documents/The_Lost_Diamond/broker"
mosquitto -c mosquitto.conf
```

If it says `Address already in use`, a Mosquitto is already running on port 1883 and you can use that one.

In another terminal, to watch every message:

```bash
mosquitto_sub -v -t 'lostdiamond/#'
```

That window is the protocol debugger. If a meeple says it published and nothing shows up here, the problem is the network or the program that publishes, not the rules.

The controller, from `server/`:

```bash
python3 -m lost_diamond.main --broker 127.0.0.1
```
