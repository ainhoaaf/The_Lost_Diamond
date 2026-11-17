"""A published turn, without Mosquitto.

The MQTT client is replaced by a list of messages. That is enough to check
the adapter: button → roll → UID → result → token. `LobbyGame` scripts the
engine answers; `RealGameTest` plays against the real `Game`.

    python3 -m unittest tests.test_turn
"""

from __future__ import annotations

import json
import random
import time
import unittest
from typing import Any

from lost_diamond.engine.game import Game, PlayerView, RollOutcome, StatusView, StepOutcome
from lost_diamond.mqtt_adapter import codec
from lost_diamond.mqtt_adapter import topics
from lost_diamond.mqtt_adapter.adapter import SEATS, MqttAdapter, MqttPublisher


MACS = tuple(f"AA:BB:CC:DD:EE:0{n}" for n in range(1, 3))
B2_UID = "04356946C72A81"
A2_UID = "0443E1AD872681"


class Outbox:
    def __init__(self) -> None:
        self.messages: list[dict[str, Any]] = []

    def publish(self, topic: str, body: dict[str, Any] | str, *, retain: bool = False) -> None:
        self.messages.append({"topic": topic, "body": body, "retain": retain})

    def of(self, topic: str) -> list[dict[str, Any]]:
        return [message for message in self.messages if message["topic"] == topic]

    def screen(self) -> list[str]:
        return [f"{m['body']['line1']} | {m['body']['line2']}" for m in self.of(topics.STATION_DISPLAY)]

    def sounds(self) -> list[str]:
        return [m["body"]["pattern"] for m in self.of(topics.STATION_BUZZER)]


class LobbyGame:
    """Fake Game that answers with scripted outcomes."""

    def __init__(self) -> None:
        self.seats: dict[str, str] | None = None
        self.calls = 0
        self.current = "Player_1"
        self.movements = 0
        self.steps_left = 0
        self.rolls = 0
        self.pending = RollOutcome("Player_1", 1, False, "Player_1")
        self.cells = dict(SEATS)
        self.steps: list[str] = []
        self.reject = False
        self.phase = "playing"
        self.scripted: StepOutcome | None = None

    def new_game(self, seats: dict[str, str], **_extra: Any) -> None:
        self.calls += 1
        self.seats = dict(seats)

    def roll(self, *, forced: int | None = None) -> RollOutcome:
        self.rolls += 1
        outcome = self.pending
        if forced is not None:
            outcome = RollOutcome(outcome.player, forced, outcome.blocked, outcome.next_player, list(outcome.skipped))
        self.movements = outcome.value
        self.steps_left = 0 if outcome.blocked else outcome.value
        self.current = outcome.next_player
        return outcome

    def remaining(self) -> int:
        return self.steps_left

    def winner(self) -> str | None:
        return None

    def step(self, cell: str) -> StepOutcome:
        self.steps.append(cell)
        if self.reject:
            return StepOutcome(
                False, "destino_ilegal", self.cells[self.current], self.steps_left,
                None, False, False, self.current,
            )
        if self.scripted is not None:
            outcome = self.scripted
            if outcome.ok:
                self.cells[self.current] = outcome.cell
                self.steps_left = outcome.remaining
                if outcome.remaining == 0 and not outcome.extra_roll:
                    self.current = outcome.next_player
                if outcome.won:
                    self.phase = "finished"
            return outcome
        self.cells[self.current] = cell
        self.steps_left = 2
        return StepOutcome(True, "", cell, 2, None, False, False, self.current)

    def status(self) -> StatusView:
        return StatusView(self.current, False, None, self.phase, None, self.movements, self.steps_left)

    def player_state(self, player_id: str) -> PlayerView:
        return PlayerView(player_id, SEATS[player_id], self.cells[player_id], False, False, False)


class BlankGame(Game):
    """Real Game where Player_1 opens and every token is blank."""

    def new_game(self, seats: dict[str, str], **_extra: Any) -> None:
        super().new_game(seats, first_player="Player_1")
        for tile in self._tiles.values():  # noqa: SLF001
            tile.kind = "blank"


def _join(mac: str) -> dict[str, Any]:
    return {"action": "join", "mac": mac, "player_id": "", "event_id": "1", "timestamp": 1}


def _button() -> dict[str, Any]:
    return {"action": "button", "pressed": True, "player_id": "", "event_id": "9", "timestamp": 1}


def _move(event_id: str, player: str = "Player_1", uid: str = "", cell: str = "") -> dict[str, Any]:
    return {
        "action": "move",
        "event_id": event_id,
        "player_id": player,
        "timestamp": 1,
        "uid": uid,
        "cell": cell,
    }


class Clock:
    def __init__(self, now: int = 0) -> None:
        self.now = now

    def __call__(self) -> int:
        return self.now


def _seat(game: Any, clock=None) -> tuple[MqttAdapter, Outbox]:
    outbox = Outbox()
    adapter = MqttAdapter(game, outbox, clock=clock or (lambda: 1000))
    for mac in MACS:
        adapter.on_message(topics.JOIN, _join(mac))
    outbox.messages.clear()
    return adapter, outbox


class CodecTest(unittest.TestCase):
    def test_game_status_carries_mac_and_remaining(self) -> None:
        body = codec.game_status(
            current_player="Player_2",
            current_mac="AA:BB:CC:DD:EE:02",
            diamond_found=False,
            carrier=None,
            movements=3,
            remaining=2,
            token=None,
        )
        self.assertEqual(body["current_mac"], "AA:BB:CC:DD:EE:02")
        self.assertEqual(body["remaining"], 2)
        self.assertIsNone(body["token"])

    def test_move_and_result_share_the_event_id(self) -> None:
        sent = codec.move("4", 1710000004, "Player_1", B2_UID)
        answer = codec.result("4", 1710000005, "Player_1", True, "", "B2", 1)
        self.assertEqual(sent["event_id"], answer["event_id"])
        self.assertEqual(answer["remaining"], 1)

    def test_player_topics_use_player_id(self) -> None:
        self.assertEqual(topics.player_move("Player_1"), "lostdiamond/Players/Player_1/move")
        self.assertEqual(topics.GAME_STATUS, "lostdiamond/Game_status")


class LobbyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.outbox = Outbox()
        self.game = LobbyGame()
        self.adapter = MqttAdapter(self.game, self.outbox, clock=lambda: 1000)

    def test_clear_retained_empties_the_previous_game(self) -> None:
        self.adapter.clear_retained()
        cleared = [message["topic"] for message in self.outbox.messages]
        self.assertIn(topics.GAME_STATUS, cleared)
        for player in SEATS:
            self.assertIn(topics.player_state(player), cleared)
        self.assertTrue(all(message["body"] == "" and message["retain"] for message in self.outbox.messages))

    def test_first_join_assigns_player_1_at_home(self) -> None:
        self.adapter.on_message(topics.JOIN, _join("aa:bb:cc:dd:ee:01"))
        sent = self.outbox.of(topics.assign("AA:BB:CC:DD:EE:01"))
        self.assertEqual(len(sent), 1)
        self.assertEqual(sent[0]["body"]["player_id"], "Player_1")
        self.assertEqual(sent[0]["body"]["home"], "A1")
        self.assertEqual(sent[0]["body"]["token"], "ld-Player_1")
        self.assertEqual(self.game.calls, 0)

    def test_same_mac_keeps_the_same_player(self) -> None:
        self.adapter.on_message(topics.JOIN, _join(MACS[0]))
        self.adapter.on_message(topics.JOIN, _join(MACS[0].lower()))
        sent = self.outbox.of(topics.assign(MACS[0]))
        self.assertEqual([message["body"]["player_id"] for message in sent], ["Player_1", "Player_1"])
        self.assertEqual(self.game.calls, 0)

    def test_second_join_starts_the_game_once(self) -> None:
        for mac in MACS:
            self.adapter.on_message(topics.JOIN, _join(mac))
        self.adapter.on_message(topics.JOIN, _join("AA:BB:CC:DD:EE:05"))
        self.assertEqual(self.game.calls, 1)
        self.assertEqual(self.game.seats, SEATS)
        self.assertEqual(self.outbox.of(topics.assign("AA:BB:CC:DD:EE:05")), [])
        status = self.outbox.of(topics.GAME_STATUS)[-1]
        self.assertTrue(status["retain"])
        self.assertEqual(status["body"]["current_player"], "Player_1")
        self.assertEqual(status["body"]["current_mac"], MACS[0])
        turns = {
            player: self.outbox.of(topics.player_state(player))[-1]["body"]["turn"]
            for player in SEATS
        }
        self.assertEqual(turns, {"Player_1": 1, "Player_2": 0})
        self.assertEqual(status["body"]["num_players"], 2)

    def test_rejoining_board_can_reuse_its_event_ids(self) -> None:
        adapter, outbox = _seat(self.game)
        adapter.on_message(topics.player_move("Player_1"), _move("2", cell="A2"))
        adapter.on_message(topics.JOIN, _join(MACS[0]))
        adapter.on_message(topics.player_move("Player_1"), _move("2", cell="A3"))
        self.assertEqual(self.game.steps, ["A2", "A3"])


class ButtonTest(unittest.TestCase):
    def test_button_publishes_the_roll(self) -> None:
        game = LobbyGame()
        game.pending = RollOutcome("Player_1", 3, False, "Player_1")
        adapter, outbox = _seat(game)
        adapter.on_message(topics.STATION_BUTTON, _button())
        self.assertEqual(game.rolls, 1)
        status = outbox.of(topics.GAME_STATUS)[-1]
        self.assertEqual(status["body"]["movements"], 3)
        self.assertEqual(status["body"]["remaining"], 3)
        self.assertEqual(status["body"]["current_player"], "Player_1")
        self.assertTrue(status["retain"])
        self.assertEqual(outbox.of(topics.STATION_DISPLAY), [{
            "topic": topics.STATION_DISPLAY,
            "body": {"line1": "Player_1", "line2": "Roll: 3", "diamond": False},
            "retain": False,
        }])
        self.assertEqual(outbox.sounds(), ["dice"])

    def test_second_press_with_an_open_roll_does_not_roll_again(self) -> None:
        game = LobbyGame()
        game.pending = RollOutcome("Player_1", 3, False, "Player_1")
        adapter, outbox = _seat(game)
        adapter.on_message(topics.STATION_BUTTON, _button())
        adapter.on_message(topics.STATION_BUTTON, _button())
        self.assertEqual(game.rolls, 1)
        self.assertEqual(outbox.screen()[-1], "Player_1 | Steps left: 3")

    def test_blocked_roll_names_who_plays_next(self) -> None:
        game = LobbyGame()
        game.pending = RollOutcome("Player_1", 2, True, "Player_2")
        adapter, outbox = _seat(game)
        adapter.on_message(topics.STATION_BUTTON, _button())
        self.assertEqual(outbox.screen(), ["Player_1 | Rolled 2, no moves. Next: Player_2"])
        status = outbox.of(topics.GAME_STATUS)[-1]["body"]
        self.assertEqual(status["current_player"], "Player_2")
        self.assertEqual(status["remaining"], 0)

    def test_skipped_players_are_announced_as_shipwreck(self) -> None:
        game = LobbyGame()
        game.pending = RollOutcome("Player_1", 2, True, "Player_3", ["Player_2"])
        adapter, outbox = _seat(game)
        adapter.on_message(topics.STATION_BUTTON, _button())
        self.assertEqual(outbox.screen(), [
            "Player_1 | Rolled 2, no moves. Next: Player_3",
            "Player_2 | Shipwreck. Next: Player_3",
        ])

    def test_button_before_the_fourth_join_does_nothing(self) -> None:
        game = LobbyGame()
        outbox = Outbox()
        adapter = MqttAdapter(game, outbox, clock=lambda: 1000)
        adapter.on_message(topics.STATION_BUTTON, _button())
        self.assertEqual(game.rolls, 0)
        self.assertEqual(outbox.messages, [])


class MoveTest(unittest.TestCase):
    def test_new_uid_calls_game_step(self) -> None:
        game = LobbyGame()
        adapter, outbox = _seat(game)
        adapter.on_message(topics.player_move("Player_1"), _move("4", uid="04 35 69 46 C7 2A 81"))
        self.assertEqual(game.steps, ["B2"])
        answer = outbox.of(topics.player_result("Player_1"))[0]["body"]
        self.assertEqual(answer["event_id"], "4")
        self.assertTrue(answer["ok"])
        self.assertEqual(answer["cell"], "B2")
        self.assertEqual(answer["remaining"], 2)

    def test_cell_is_used_when_the_twin_sends_it(self) -> None:
        game = LobbyGame()
        adapter, _outbox = _seat(game)
        adapter.on_message(topics.player_move("Player_1"), _move("4", cell="e1"))
        self.assertEqual(game.steps, ["E1"])

    def test_same_uid_is_ignored(self) -> None:
        game = LobbyGame()
        adapter, outbox = _seat(game)
        adapter.on_message(topics.player_move("Player_1"), _move("4", uid=B2_UID))
        adapter.on_message(topics.player_move("Player_1"), _move("5", uid=B2_UID))
        self.assertEqual(game.steps, ["B2"])
        answers = outbox.of(topics.player_result("Player_1"))
        self.assertEqual([item["body"]["event_id"] for item in answers], ["4", "5"])
        self.assertEqual(answers[1]["body"]["cell"], "B2")

    def test_same_uid_counts_again_on_a_new_roll(self) -> None:
        game = LobbyGame()
        adapter, _outbox = _seat(game)
        adapter.on_message(topics.player_move("Player_1"), _move("4", uid=B2_UID))
        game.cells["Player_1"] = "A1"
        game.steps_left = 0
        adapter.on_message(topics.STATION_BUTTON, _button())
        adapter.on_message(topics.player_move("Player_1"), _move("5", uid=B2_UID))
        self.assertEqual(game.steps, ["B2", "B2"])

    def test_back_on_the_current_cell_spends_nothing(self) -> None:
        game = LobbyGame()
        game.pending = RollOutcome("Player_1", 2, False, "Player_1")
        adapter, outbox = _seat(game)
        adapter.on_message(topics.STATION_BUTTON, _button())
        adapter.on_message(topics.player_move("Player_1"), _move("4", cell="A1"))
        self.assertEqual(game.steps, [])
        answer = outbox.of(topics.player_result("Player_1"))[0]["body"]
        self.assertEqual((answer["ok"], answer["cell"], answer["remaining"]), (True, "A1", 2))

    def test_same_event_id_is_answered_once(self) -> None:
        game = LobbyGame()
        adapter, outbox = _seat(game)
        body = _move("4", cell="A2")
        adapter.on_message(topics.player_move("Player_1"), body)
        adapter.on_message(topics.player_move("Player_1"), body)
        self.assertEqual(game.steps, ["A2"])
        answers = outbox.of(topics.player_result("Player_1"))
        self.assertEqual(answers[0]["body"], answers[1]["body"])

    def test_another_player_can_reuse_the_same_event_id(self) -> None:
        game = LobbyGame()
        adapter, outbox = _seat(game)
        adapter.on_message(topics.player_move("Player_1"), _move("2", cell="A2"))
        adapter.on_message(topics.player_move("Player_2"), _move("2", player="Player_2", cell="C1"))
        self.assertEqual(game.steps, ["A2"])
        answer = outbox.of(topics.player_result("Player_2"))[0]["body"]
        self.assertEqual(answer["player_id"], "Player_2")
        self.assertFalse(answer["ok"])
        self.assertEqual(answer["reason"], "no_es_tu_turno")

    def test_illegal_step_publishes_the_reason_and_stays(self) -> None:
        game = LobbyGame()
        game.reject = True
        adapter, outbox = _seat(game)
        adapter.on_message(topics.player_move("Player_1"), _move("4", cell="B1"))
        answer = outbox.of(topics.player_result("Player_1"))[0]["body"]
        self.assertFalse(answer["ok"])
        self.assertEqual(answer["reason"], "destino_ilegal")
        self.assertEqual(answer["cell"], "A1")
        self.assertEqual(game.cells["Player_1"], "A1")
        self.assertEqual(outbox.screen()[-1], "Player_1 | Illegal move")

    def test_unknown_uid_does_not_step(self) -> None:
        game = LobbyGame()
        adapter, outbox = _seat(game)
        adapter.on_message(topics.player_move("Player_1"), _move("4", uid="04FFFFFFFFFFFF"))
        self.assertEqual(game.steps, [])
        answer = outbox.of(topics.player_result("Player_1"))[0]["body"]
        self.assertFalse(answer["ok"])
        self.assertEqual(answer["reason"], "uid_desconocido")
        self.assertEqual(answer["cell"], "A1")
        self.assertEqual(outbox.screen()[-1], "Player_1 | Unknown tag")


def _landed(token: str, *, extra_roll: bool = False, won: bool = False, cell: str = "B2") -> StepOutcome:
    return StepOutcome(True, "", cell, 0, token, extra_roll, won, "Player_2")


class FinishTest(unittest.TestCase):
    def test_zero_remaining_publishes_the_token(self) -> None:
        game = LobbyGame()
        game.scripted = _landed("diamond", cell="A2")
        adapter, outbox = _seat(game)
        adapter.on_message(topics.player_move("Player_1"), _move("4", cell="A2"))
        status = outbox.of(topics.GAME_STATUS)[-1]["body"]
        self.assertEqual(status["token"], "diamond")
        self.assertEqual(status["remaining"], 0)
        self.assertEqual(status["phase"], "playing")
        self.assertEqual(game.rolls, 0)
        self.assertEqual(outbox.screen(), ["Player_1 | Token: diamond. Next: Player_2"])
        self.assertEqual(outbox.sounds(), ["diamond"])

    def test_extra_roll_happens_without_a_button(self) -> None:
        game = LobbyGame()
        game.scripted = _landed("coin", extra_roll=True)
        game.pending = RollOutcome("Player_1", 2, False, "Player_1")
        adapter, outbox = _seat(game)
        adapter.on_message(topics.player_move("Player_1"), _move("4", cell="B2"))
        self.assertEqual(game.rolls, 1)
        statuses = [item["body"] for item in outbox.of(topics.GAME_STATUS)]
        self.assertEqual(statuses[0]["token"], "coin")
        self.assertEqual(statuses[0]["remaining"], 0)
        self.assertEqual(statuses[-1]["movements"], 2)
        self.assertEqual(statuses[-1]["remaining"], 2)
        self.assertIsNone(statuses[-1]["token"])
        self.assertEqual(outbox.screen(), ["Player_1 | Token: coin. Roll again", "Player_1 | Roll: 2"])

    def test_a_win_finishes_the_phase(self) -> None:
        game = LobbyGame()
        game.scripted = _landed("blank", won=True, cell="C4")
        game.pending = RollOutcome("Player_1", 3, False, "Player_1")
        adapter, outbox = _seat(game)
        adapter.on_message(topics.player_move("Player_1"), _move("4", cell="C4"))
        self.assertEqual(game.rolls, 0)
        status = outbox.of(topics.GAME_STATUS)[-1]["body"]
        self.assertEqual(status["phase"], "finished")
        self.assertEqual(status["token"], "blank")
        self.assertEqual(outbox.screen()[-1], "Player_1 | Player_1 wins!")
        adapter.on_message(topics.STATION_BUTTON, _button())
        self.assertEqual(game.rolls, 0)


class IdleTest(unittest.TestCase):
    def test_default_clock_counts_milliseconds(self) -> None:
        adapter = MqttAdapter(LobbyGame(), Outbox())
        self.assertLess(abs(adapter.clock() - time.time() * 1000), 5_000)

    def test_idle_warning_does_not_end_the_turn(self) -> None:
        clock = Clock()
        game = LobbyGame()
        game.pending = RollOutcome("Player_1", 3, False, "Player_1")
        adapter, outbox = _seat(game, clock)
        adapter.on_message(topics.STATION_BUTTON, _button())
        clock.now = 14_999
        adapter.poll()
        self.assertEqual(outbox.sounds(), ["dice"])
        clock.now = 15_000
        adapter.poll()
        adapter.poll()
        self.assertEqual(outbox.sounds(), ["dice", "hurry"])
        self.assertEqual(game.rolls, 1)
        self.assertFalse(adapter._finished)

    def test_a_new_uid_restarts_the_wait(self) -> None:
        clock = Clock()
        game = LobbyGame()
        game.pending = RollOutcome("Player_1", 3, False, "Player_1")
        adapter, outbox = _seat(game, clock)
        adapter.on_message(topics.STATION_BUTTON, _button())
        clock.now = 10_000
        adapter.on_message(topics.player_move("Player_1"), _move("4", uid=B2_UID))
        clock.now = 20_000
        adapter.poll()
        self.assertNotIn("hurry", outbox.sounds())
        clock.now = 25_000
        adapter.poll()
        self.assertEqual(outbox.sounds().count("hurry"), 1)

    def test_the_same_uid_does_not_restart_the_wait(self) -> None:
        clock = Clock()
        game = LobbyGame()
        game.pending = RollOutcome("Player_1", 3, False, "Player_1")
        adapter, outbox = _seat(game, clock)
        adapter.on_message(topics.STATION_BUTTON, _button())
        clock.now = 1_000
        adapter.on_message(topics.player_move("Player_1"), _move("4", uid=B2_UID))
        clock.now = 10_000
        adapter.on_message(topics.player_move("Player_1"), _move("5", uid=B2_UID))
        clock.now = 16_000
        adapter.poll()
        self.assertEqual(outbox.sounds().count("hurry"), 1)

    def test_a_blocked_roll_does_not_start_the_wait(self) -> None:
        clock = Clock()
        game = LobbyGame()
        game.pending = RollOutcome("Player_1", 2, True, "Player_2")
        adapter, outbox = _seat(game, clock)
        adapter.on_message(topics.STATION_BUTTON, _button())
        clock.now = 20_000
        adapter.poll()
        self.assertEqual(outbox.sounds(), [])


class RealGameTest(unittest.TestCase):
    """The adapter against the real engine, all tokens blank."""

    def setUp(self) -> None:
        self.game = BlankGame(rng=random.Random(3))
        self.adapter, self.outbox = _seat(self.game)

    def press(self, value: int) -> None:
        self.game.roll = _forced(self.game.roll, value)  # type: ignore[method-assign]
        self.adapter.on_message(topics.STATION_BUTTON, _button())

    def move(self, event_id: str, player: str, **where: str) -> dict[str, Any]:
        self.adapter.on_message(topics.player_move(player), _move(event_id, player, **where))
        return self.outbox.of(topics.player_result(player))[-1]["body"]

    def test_a_full_turn_passes_to_player_2(self) -> None:
        self.press(2)
        self.assertEqual(self.move("2", "Player_1", uid=A2_UID)["remaining"], 1)
        last = self.move("3", "Player_1", cell="A3")
        self.assertEqual((last["ok"], last["cell"], last["remaining"]), (True, "A3", 0))
        status = self.outbox.of(topics.GAME_STATUS)[-1]["body"]
        self.assertEqual((status["current_player"], status["current_mac"]), ("Player_2", MACS[1]))
        self.assertEqual(status["token"], "blank")
        self.assertIn("Player_1 | Token: blank. Next: Player_2", self.outbox.screen())

    def test_engine_rejections_reach_the_meeple_and_the_screen(self) -> None:
        self.press(1)
        answer = self.move("2", "Player_1", cell="B2")
        self.assertEqual((answer["ok"], answer["reason"], answer["cell"]), (False, "destino_ilegal", "A1"))
        self.assertEqual(self.outbox.screen()[-1], "Player_1 | Illegal move")
        self.assertTrue(self.move("3", "Player_1", cell="A2")["ok"])

    def test_occupied_cell_is_reported(self) -> None:
        self.game._players["Player_2"].cell = "A2"  # noqa: SLF001
        self.press(1)
        answer = self.move("2", "Player_1", cell="A2")
        self.assertEqual(answer["reason"], "ocupada")
        self.assertEqual(self.outbox.screen()[-1], "Player_1 | Cell taken")

    def test_moving_before_the_roll_asks_for_the_button(self) -> None:
        answer = self.move("2", "Player_1", cell="A2")
        self.assertEqual(answer["reason"], "sin_tirada")
        self.assertEqual(self.outbox.screen()[-1], "Player_1 | Press the button")

    def test_double_press_does_not_crash(self) -> None:
        self.press(2)
        self.adapter.on_message(topics.STATION_BUTTON, _button())
        self.assertEqual(self.game.remaining(), 2)
        self.assertEqual(self.outbox.screen()[-1], "Player_1 | Steps left: 2")


def _forced(roll, value: int):
    def once(*, forced: int | None = None) -> RollOutcome:
        return roll(forced=value if forced is None else forced)

    return once


class PublisherTest(unittest.TestCase):
    def test_state_is_json_qos1_and_clear_stays_empty(self) -> None:
        sent: list[tuple] = []

        class Client:
            def publish(self, topic: str, payload: str, qos: int = 0, retain: bool = False) -> None:
                sent.append((topic, payload, qos, retain))

        publisher = MqttPublisher(Client())
        publisher.publish(topics.GAME_STATUS, {"current_player": "Player_1"}, retain=True)
        publisher.publish(topics.GAME_STATUS, "", retain=True)
        publisher.publish(topics.STATION_BUZZER, {"pattern": "hurry"})
        self.assertEqual(json.loads(sent[0][1])["current_player"], "Player_1")
        self.assertEqual(sent[0][2:], (1, True))
        self.assertEqual(sent[1][1:], ("", 1, True))
        self.assertEqual(sent[2][2:], (0, False))


if __name__ == "__main__":
    unittest.main()
