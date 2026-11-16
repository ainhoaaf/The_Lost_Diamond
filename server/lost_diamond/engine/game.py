"""A single game.

This is the only module that applies rules: the deal, turn order, the die,
every meeple hop, token effects and victory. It does not import MQTT.

Turn flow:

1. `new_game` shuffles the 14 tokens and seats two players on A1 and two on
   C4. Turns alternate between the top and the bottom home.
2. `roll` always rolls for the active player: 1, 2 or 3, stored as a step
   budget. It never returns 0. If no legal cell exists (`blocked`), the turn
   passes automatically. Players with a pending shipwreck are skipped when
   the turn passes and are listed in `skipped`.
3. `step` receives the next cell (translated from the UID). An illegal hop
   is reported and spends nothing. A legal hop subtracts its cost. The
   starting cell of the current roll cannot be revisited.
4. When the budget reaches 0, `step` reveals the token and applies it.
   Coin: another roll in the same turn, from that cell (`extra_roll`).
   Pirate, before the diamond is found: back to the player's starting home.
   Shipwreck: the player's next turn is skipped.
   Horseshoe: grants the right to win only once the diamond has been found.
5. A player wins by ending a move on A1 or C4 carrying the diamond, or
   holding the horseshoe right before the carrier gets home.
6. `status` and `player_state` are read-only. The adapter uses them to
   publish `Game_status` and `Players/Player_N`.

For tests: `Game(rng=...)`, `new_game(..., tokens=..., first_player=...)` and
`roll(forced=...)` remove randomness. Production code calls them without
those arguments.

`reason` codes (shared contract with the adapter, do not rename alone):

- `destino_ilegal`: not adjacent, bridge costs more than the remaining
  budget, the roll's starting cell, or a hop that leaves unspendable steps.
- `ocupada`: another player is on that cell and it is not a home.
- `sin_tirada`: no open roll (button not pressed yet, or game finished).

The 15-second idle warning does not live here: the adapter counts it, and it
never cancels the turn.
"""

from __future__ import annotations

import random
from collections import Counter
from dataclasses import dataclass, field

from lost_diamond.engine.board import HOMES, all_cells, hops_from
from lost_diamond.engine.tokens import POOL, playable_cells, reveal_code

DIE_FACES = (1, 2, 3)

REASON_ILLEGAL = "destino_ilegal"
REASON_OCCUPIED = "ocupada"
REASON_NO_ROLL = "sin_tirada"

PHASE_PLAYING = "playing"
PHASE_FINISHED = "finished"


class GameError(RuntimeError):
    """Out-of-order call: rolling with an open roll, playing a finished game, etc."""


@dataclass
class RollOutcome:
    player: str
    value: int
    blocked: bool
    next_player: str
    skipped: list[str] = field(default_factory=list)


@dataclass
class StepOutcome:
    ok: bool
    reason: str
    cell: str
    remaining: int
    token: str | None
    extra_roll: bool
    won: bool
    next_player: str
    skipped: list[str] = field(default_factory=list)


@dataclass
class StatusView:
    current_player: str
    diamond_found: bool
    carrier: str | None
    phase: str
    winner: str | None
    movements: int
    remaining: int


@dataclass
class PlayerView:
    id: str
    home: str
    cell: str
    has_diamond: bool
    has_horseshoe: bool
    skip: bool


@dataclass
class _Player:
    id: str
    home: str
    cell: str
    has_diamond: bool = False
    has_horseshoe: bool = False
    skip: bool = False


@dataclass
class _Tile:
    kind: str
    spent: bool = False


class Game:
    def __init__(self, rng: random.Random | None = None) -> None:
        """`rng` makes the deal and the die reproducible in tests."""
        self.rng = rng or random.Random()
        self._players: dict[str, _Player] = {}
        self._order: list[str] = []
        self._turn = 0
        self._tiles: dict[str, _Tile] = {}
        self._diamond_found = False
        self._winner: str | None = None
        # Current roll.
        self._movements = 0
        self._remaining = 0
        self._start: str | None = None
        self._rolling = False

    #  setup

    def new_game(
        self,
        seats: dict[str, str],
        *,
        tokens: dict[str, str] | None = None,
        first_player: str | None = None,
    ) -> None:
        """Shuffle the tokens and seat the players.

        `seats` maps Player_N to its home (A1 or C4), two players per home.
        `tokens` (tests only) maps cell to token and skips the shuffle.
        `first_player` (tests only) fixes who starts; otherwise a player
        from a randomly chosen home opens.
        """
        if set(seats.values()) - set(HOMES):
            raise ValueError("homes are A1 and C4")
        by_home = {h: sorted(p for p, home in seats.items() if home == h) for h in HOMES}
        if any(len(players) != 2 for players in by_home.values()):
            raise ValueError("there must be two players on A1 and two on C4")

        if first_player is None:
            first_player = by_home[self.rng.choice(HOMES)][0]
        if first_player not in seats:
            raise ValueError(f"first_player is not seated: {first_player}")

        # Turn order alternates homes: first, other home, first's mate, other home.
        first_home = seats[first_player]
        other_home = HOMES[1] if first_home == HOMES[0] else HOMES[0]
        mate = next(p for p in by_home[first_home] if p != first_player)
        self._order = [first_player, by_home[other_home][0], mate, by_home[other_home][1]]
        self._turn = 0

        self._players = {p: _Player(id=p, home=h, cell=h) for p, h in seats.items()}
        self._tiles = self._deal(tokens)
        self._diamond_found = False
        self._winner = None
        self._end_roll()

    def _deal(self, tokens: dict[str, str] | None) -> dict[str, _Tile]:
        """Place one token on each non-home cell, shuffled or as given."""
        cells = playable_cells()
        if tokens is None:
            kinds = list(POOL)
            self.rng.shuffle(kinds)
            return {cell: _Tile(kind) for cell, kind in zip(cells, kinds)}
        if set(tokens) != set(cells):
            raise ValueError("tokens must cover the 14 non-home cells")
        if Counter(tokens.values()) != Counter(POOL):
            raise ValueError("tokens does not match the POOL distribution")
        return {cell: _Tile(tokens[cell]) for cell in cells}

    #  turn

    def current_player(self) -> str:
        """Player_N whose turn it is."""
        self._require_started()
        return self._order[self._turn]

    def roll(self, *, forced: int | None = None) -> RollOutcome:
        """Roll 1-3 for the active player and store the step budget.

        `forced` (tests only) fixes the value.
        """
        self._require_started()
        if self._winner is not None:
            raise GameError("the game is already finished")
        if self._rolling:
            raise GameError("a roll is already open")
        if forced is not None and forced not in DIE_FACES:
            raise ValueError(f"the die is 1, 2 or 3: {forced}")

        value = forced if forced is not None else self.rng.choice(DIE_FACES)
        player = self._players[self.current_player()]
        self._movements = value
        self._remaining = value
        self._start = player.cell
        self._rolling = True

        if not self._can_finish(player.cell, value, player.id):
            skipped = self._pass_turn()
            return RollOutcome(player.id, value, True, self.current_player(), skipped)
        return RollOutcome(player.id, value, False, player.id, [])

    def remaining(self) -> int:
        """Steps left for the active player in this roll."""
        return self._remaining if self._rolling else 0

    def legal_next(self) -> list[str]:
        """Cells one hop away whose cost fits the remaining budget.

        Excludes the roll's starting cell, occupied cells and dead ends.
        """
        if not self._rolling:
            return []
        player = self._players[self.current_player()]
        return sorted(
            dest
            for dest, cost in hops_from(player.cell).items()
            if self._hop_reason(player.id, dest, cost, self._remaining) is None
        )

    def step(self, cell: str) -> StepOutcome:
        """Apply one hop. If illegal, `ok` is False and no steps are spent."""
        self._require_started()
        player = self._players[self.current_player()]

        if not self._rolling:
            return self._reject(player, REASON_NO_ROLL)
        if cell not in _ALL_CELLS:
            return self._reject(player, REASON_ILLEGAL)

        cost = hops_from(player.cell).get(cell)
        reason = self._hop_reason(player.id, cell, cost, self._remaining)
        if reason is not None:
            return self._reject(player, reason)

        assert cost is not None
        player.cell = cell
        self._remaining -= cost
        if self._remaining > 0:
            return StepOutcome(True, "", cell, self._remaining, None, False, False, player.id)

        self._rolling = False
        return self._land(player)

    def winner(self) -> str | None:
        """Player_N if someone has won, otherwise None."""
        return self._winner

    #  read-only

    def status(self) -> StatusView:
        """Game state, published as `Game_status`."""
        self._require_started()
        carrier = next((p.id for p in self._players.values() if p.has_diamond), None)
        return StatusView(
            current_player=self.current_player(),
            diamond_found=self._diamond_found,
            carrier=carrier,
            phase=PHASE_FINISHED if self._winner else PHASE_PLAYING,
            winner=self._winner,
            movements=self._movements,
            remaining=self._remaining if self._rolling else 0,
        )

    def player_state(self, player_id: str) -> PlayerView:
        """Player state, published as `Players/Player_N`."""
        p = self._players[player_id]
        return PlayerView(p.id, p.home, p.cell, p.has_diamond, p.has_horseshoe, p.skip)

    #  internal

    def _require_started(self) -> None:
        if not self._order:
            raise GameError("new_game has not been called")

    def _end_roll(self) -> None:
        self._movements = 0
        self._remaining = 0
        self._start = None
        self._rolling = False
    


    def _pass_turn(self) -> list[str]:
        """Advance to the next player."""
        self._end_roll()
        self._turn = (self._turn + 1) % len(self._order)
        return []

    def _reject(self, player: _Player, reason: str) -> StepOutcome:
        return StepOutcome(False, reason, player.cell, self.remaining(), None, False, False, player.id)

    def _occupied_by_other(self, cell: str, player_id: str) -> bool:
        if cell in HOMES:
            return False
        return any(p.cell == cell for p in self._players.values() if p.id != player_id)

    def _hop_reason(self, player_id: str, dest: str, cost: int | None, budget: int) -> str | None:
        """None if the hop is legal, otherwise its `reason` code."""
        if cost is None or cost > budget or dest == self._start:
            return REASON_ILLEGAL
        if self._occupied_by_other(dest, player_id):
            return REASON_OCCUPIED
        if not self._can_finish(dest, budget - cost, player_id):
            return REASON_ILLEGAL
        return None

    def _can_finish(self, cell: str, budget: int, player_id: str) -> bool:
        """Can exactly `budget` steps be spent from `cell`? (DFS, depth <= 3)"""
        if budget == 0:
            return True
        return any(
            cost <= budget
            and dest != self._start
            and not self._occupied_by_other(dest, player_id)
            and self._can_finish(dest, budget - cost, player_id)
            for dest, cost in hops_from(cell).items()
        )

    def _land(self, player: _Player) -> StepOutcome:
        """Budget reached 0: reveal, apply the token and pass the turn."""
        token, extra_roll = self._apply_token(player)
        skipped = [] if extra_roll else self._pass_turn()
        return StepOutcome(True, "", player.cell, 0, token, extra_roll, False, self.current_player(), skipped)

    def _apply_token(self, player: _Player) -> tuple[str, bool]:
        """Return (code, extra_roll). May move the player (pirate)."""
        if player.cell in HOMES:
            return "blank", False

        tile = self._tiles[player.cell]

        if tile.kind == "diamond":
            player.has_diamond = True
            self._diamond_found = True
            tile.kind = "blank"
            return "diamond", False

        if tile.kind == "pirate":
            if self._diamond_found:
                return "pirate_off", False
            player.cell = player.home
            return "pirate", False

        if tile.kind == "horseshoe":
            valid = not tile.spent and self._diamond_found and not player.has_diamond
            tile.spent = True
            if valid:
                player.has_horseshoe = True
                return "horseshoe", False
            return "horseshoe_off", False

        if tile.kind == "coin":
            code = reveal_code("coin", diamond_found=self._diamond_found, spent=tile.spent)
            tile.spent = True
            return code, code == "coin"

        if tile.kind == "shipwreck":
            player.skip = True
            return "shipwreck", False

        return "blank", False


_ALL_CELLS = frozenset(all_cells())