"""Connects the broker to `engine.Game`.

This is the only file that talks to Mosquitto. It receives facts from the
boards and publishes what the screen, the LED and the buzzer must do. It
never applies a rule itself: every decision comes from `Game`.

- `clear_retained` wipes the retained state of the previous game.
- `lobby/join` assigns Player_1 and Player_2 in MAC arrival order. The same
  MAC gets the same player back.
- On the second player it calls `Game.new_game` and publishes `Game_status`
  and `Players/Player_N`.
- `Station/button` calls `Game.roll` and publishes the value. A press while
  a roll is still open only repeats how many steps are left. A blocked roll
  announces who loses the turn, and shipwreck skips are announced too.
- `Players/Player_N/move` translates the UID (or takes the cell), calls
  `Game.step` and answers on `result` with the same `event_id`.
- When `remaining` reaches 0 it publishes the `token`. On `extra_roll` it
  rolls again without the button. On `won` the phase becomes `finished`.
- `poll` counts 15 seconds since the roll or the last new UID. It then
  plays `hurry` on the buzzer and the turn stays open.
- `start` connects to Mosquitto, clears retained messages and listens.
"""

from __future__ import annotations

import json
import time
from typing import Any, Protocol

from lost_diamond.engine.game import Game, GameError, RollOutcome
from lost_diamond.mqtt_adapter import codec, topics
from lost_diamond.nfc import cell_for, normalize

SEATS = {
    "Player_1": "A1",
    "Player_2": "C4",
}
PLAYERS = tuple(SEATS)
IDLE_MS = 15_000

REASON_NOT_YOUR_TURN = "no_es_tu_turno"
REASON_UNKNOWN_UID = "uid_desconocido"

SCREEN_REASONS = {
    "destino_ilegal": "Illegal move",
    "ocupada": "Cell taken",
    "sin_tirada": "Press the button",
    REASON_UNKNOWN_UID: "Unknown tag",
}

TOKEN_SOUNDS = {"diamond": "diamond", "horseshoe": "horseshoe"}


def _now_ms() -> int:
    return int(time.time() * 1000)


class Publisher(Protocol):
    def publish(self, topic: str, body: dict[str, Any] | str, *, retain: bool = False) -> None:
        """Publish a JSON body (dict) or an empty payload (str) that clears a retained message."""


class MqttPublisher:
    """Publishes with paho. State goes out at QoS 1, screen and buzzer at QoS 0."""

    def __init__(self, client: Any) -> None:
        self.client = client

    def publish(self, topic: str, body: dict[str, Any] | str, *, retain: bool = False) -> None:
        payload = body if isinstance(body, str) else json.dumps(body, ensure_ascii=False)
        quiet = topic in (topics.STATION_DISPLAY, topics.STATION_BUZZER)
        self.client.publish(topic, payload, qos=0 if quiet else 1, retain=retain)


class MqttAdapter:
    def __init__(self, game: Game, publisher: Publisher | None = None, clock=None) -> None:
        """`clock` returns milliseconds. Tests pass a fake one."""
        self.game = game
        self.publisher = publisher
        self.clock = clock or _now_ms
        self.by_mac: dict[str, str] = {}
        self.started = False
        self._event = 0
        self._results: dict[tuple[str, str], dict[str, Any]] = {}
        self._last_uid: dict[str, str] = {}
        self._token: str | None = None
        self._finished = False
        self._idle_from: int | None = None
        self._hurried = False

    def clear_retained(self) -> None:
        """Clear Game_status, both player states and, once known, the
        lobby/status of their MACs."""
        targets = [topics.GAME_STATUS]
        targets.extend(topics.player_state(player) for player in PLAYERS)
        targets.extend(topics.lobby_status(mac) for mac in self.by_mac)
        for topic in targets:
            self.publisher.publish(topic, "", retain=True)

    def on_message(self, topic: str, body: dict[str, Any]) -> None:
        action = body.get("action")
        if topic == topics.JOIN or action == "join":
            self._on_join(body)
        elif topic == topics.STATION_BUTTON or action == "button":
            self._on_button()
        elif action == "move" or topic.endswith("/move"):
            self._on_move(topic, body)

    def start(self, host: str = "127.0.0.1", port: int = 1883) -> None:
        """Connect to Mosquitto, clear the previous game and listen."""
        import paho.mqtt.client as mqtt

        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        client.on_message = self._on_mqtt
        client.connect(host, port, keepalive=60)
        client.subscribe(topics.JOIN, qos=1)
        client.subscribe(topics.STATION_BUTTON, qos=1)
        client.subscribe(f"{topics.PREFIX}/Players/+/move", qos=1)
        self.publisher = MqttPublisher(client)
        self.clear_retained()
        client.loop(timeout=1.0)
        print(f"Listening on {host}:{port}. Ctrl+C to stop.")
        try:
            while True:
                client.loop(timeout=0.2)
                self.poll()
        except KeyboardInterrupt:
            client.disconnect()

    def poll(self) -> None:
        """Play `hurry` once if the roll is out and no new UID arrived for 15 s."""
        if self._idle_from is None or self._hurried or self._finished:
            return
        if self.clock() - self._idle_from < IDLE_MS:
            return
        self.publisher.publish(topics.STATION_BUZZER, codec.buzzer("hurry"))
        self._hurried = True

    def mac_of(self, player_id: str) -> str:
        for mac, player in self.by_mac.items():
            if player == player_id:
                return mac
        return ""

    def publish_state(self) -> None:
        """Publish the retained state the boards read when they connect."""
        status = self.game.status()
        finished = self._finished or status.phase == "finished"
        self.publisher.publish(
            topics.GAME_STATUS,
            codec.game_status(
                current_player=status.current_player,
                current_mac=self.mac_of(status.current_player),
                diamond_found=status.diamond_found,
                carrier=status.carrier,
                movements=status.movements,
                remaining=status.remaining,
                token=self._token,
                phase="finished" if finished else status.phase,
                num_players=len(PLAYERS),
            ),
            retain=True,
        )
        for player in PLAYERS:
            view = self.game.player_state(player)
            self.publisher.publish(
                topics.player_state(player),
                codec.player_state(
                    player_id=view.id,
                    home=view.home,
                    cell=view.cell,
                    turn=1 if player == status.current_player and not finished else 0,
                    movements=status.movements,
                    has_diamond=view.has_diamond,
                    has_horseshoe=view.has_horseshoe,
                    skip=view.skip,
                ),
                retain=True,
            )

    def _on_mqtt(self, client: Any, userdata: Any, message: Any) -> None:
        raw = message.payload.decode("utf-8")
        if not raw:
            return
        try:
            body = json.loads(raw)
        except json.JSONDecodeError:
            return
        if isinstance(body, dict):
            self.on_message(message.topic, body)

    def _on_join(self, body: dict[str, Any]) -> None:
        mac = str(body.get("mac") or "").strip().upper()
        if not mac:
            return
        if mac in self.by_mac:
            self._forget_results(self.by_mac[mac])
        else:
            if len(self.by_mac) >= len(PLAYERS):
                return
            self.by_mac[mac] = PLAYERS[len(self.by_mac)]
        player = self.by_mac[mac]
        event_id, timestamp = self._next_event()
        self.publisher.publish(
            topics.assign(mac),
            codec.assign(event_id, timestamp, player, SEATS[player], f"ld-{player}"),
        )
        if len(self.by_mac) == len(PLAYERS) and not self.started:
            self.game.new_game(dict(SEATS))
            self.started = True
            self.publish_state()

    def _on_button(self) -> None:
        if not self.started or self._finished:
            return
        if self.game.remaining() > 0:
            status = self.game.status()
            self._display(status.current_player, f"Steps left: {status.remaining}")
            return
        try:
            outcome = self.game.roll()
        except GameError:
            return
        self._apply_roll(outcome)

    def _apply_roll(self, outcome: RollOutcome) -> None:
        self._token = None
        self._last_uid.pop(outcome.player, None)
        self._announce_roll(outcome)
        self.publish_state()
        if outcome.blocked:
            self._disarm_idle()
        else:
            self._arm_idle()

    def _announce_roll(self, outcome: RollOutcome) -> None:
        if outcome.blocked:
            self._display(outcome.player, f"Rolled {outcome.value}, no moves. Next: {outcome.next_player}")
        else:
            self._display(outcome.player, f"Roll: {outcome.value}")
            self._buzz("dice")
        for player in outcome.skipped:
            self._display(player, f"Shipwreck. Next: {outcome.next_player}")

    def _on_move(self, topic: str, body: dict[str, Any]) -> None:
        if not self.started:
            return
        player = str(body.get("player_id") or "") or self._player_from_topic(topic)
        if player not in SEATS:
            return
        event_id = str(body.get("event_id") or "")
        remembered = self._results.get((player, event_id))
        if event_id and remembered is not None:
            self.publisher.publish(topics.player_result(player), remembered)
            return
        here = self.game.player_state(player).cell
        if self._finished or player != self.game.status().current_player:
            self._reply(player, event_id, False, REASON_NOT_YOUR_TURN, here, self.game.remaining())
            return
        cell = str(body.get("cell") or "").strip().upper()
        uid = str(body.get("uid") or "").strip()
        if not cell and uid:
            seen = normalize(uid)
            if self._last_uid.get(player) == seen:
                self._reply(player, event_id, True, "", here, self.game.remaining())
                return
            found = cell_for(uid)
            if found is None:
                self._arm_idle()
                self._display(player, SCREEN_REASONS[REASON_UNKNOWN_UID])
                self._reply(player, event_id, False, REASON_UNKNOWN_UID, here, self.game.remaining())
                return
            self._last_uid[player] = seen
            cell = found
        if not cell:
            return
        self._arm_idle()
        if cell == here and self.game.remaining() > 0:
            self._reply(player, event_id, True, "", here, self.game.remaining())
            return
        outcome = self.game.step(cell)
        self._reply(player, event_id, outcome.ok, outcome.reason, outcome.cell, outcome.remaining)
        if not outcome.ok:
            self._display(player, SCREEN_REASONS.get(outcome.reason, outcome.reason))
            self.publish_state()
            return
        if outcome.remaining == 0:
            self._land(player, outcome)
        self.publish_state()
        if self._finished:
            return
        if outcome.extra_roll:
            self._apply_roll(self.game.roll())
        elif outcome.remaining == 0:
            self._disarm_idle()

    def _land(self, player: str, outcome: Any) -> None:
        self._token = outcome.token
        if outcome.won or self.game.winner() is not None:
            self._finished = True
            self._disarm_idle()
            self._display(player, f"{player} wins!")
        elif outcome.extra_roll:
            self._display(player, f"Token: {outcome.token}. Roll again")
        else:
            self._display(player, f"Token: {outcome.token}. Next: {outcome.next_player}")
        if outcome.token in TOKEN_SOUNDS:
            self._buzz(TOKEN_SOUNDS[outcome.token])
        for skipped in outcome.skipped:
            self._display(skipped, f"Shipwreck. Next: {outcome.next_player}")

    def _reply(
        self,
        player: str,
        event_id: str,
        ok: bool,
        reason: str,
        cell: str,
        remaining: int,
    ) -> None:
        body = codec.result(event_id, self._timestamp(), player, ok, reason, cell, remaining)
        if event_id:
            self._results[(player, event_id)] = body
        self.publisher.publish(topics.player_result(player), body)

    def _forget_results(self, player: str) -> None:
        """A board that rejoins restarts its event_id counter."""
        for key in [key for key in self._results if key[0] == player]:
            del self._results[key]
        self._last_uid.pop(player, None)

    def _player_from_topic(self, topic: str) -> str:
        parts = topic.split("/")
        if len(parts) >= 2 and parts[-1] == "move":
            return parts[-2]
        return ""

    def _arm_idle(self) -> None:
        if self._finished:
            return
        self._idle_from = self.clock()
        self._hurried = False

    def _disarm_idle(self) -> None:
        self._idle_from = None
        self._hurried = False

    def _display(self, line1: str, line2: str) -> None:
        diamond = self.game.status().diamond_found if self.started else False
        self.publisher.publish(topics.STATION_DISPLAY, codec.display(line1, line2, diamond=diamond))

    def _buzz(self, pattern: str) -> None:
        self.publisher.publish(topics.STATION_BUZZER, codec.buzzer(pattern))

    def _timestamp(self) -> int:
        return int(self.clock()) // 1000

    def _next_event(self) -> tuple[str, int]:
        self._event += 1
        return str(self._event), self._timestamp()
