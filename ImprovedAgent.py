from typing import List, Optional
import chess.engine
import random
from reconchess import *
from reconchess.utilities import without_opponent_pieces, is_illegal_castle
import os
from collections import defaultdict

STOCKFISH_ENV_VAR = 'STOCKFISH_PATH'

# Phase 1 — cap the candidate set at this size (roadmap says 200–500)
MAX_BOARDS = 500



class ImprovedAgent(Player):
    """
    Improved RBC agent implementing:
      - Phase 1: Particle filter belief state (candidate board set)
      - Phase 2: Uncertainty-based sense selection (maximum information gain)
      - Phase 3: Multi-board Stockfish voting for move selection
    """

    def __init__(self):
        self.possible_boards = set()
        self.color = None
        self.my_piece_captured_square = None

        if STOCKFISH_ENV_VAR not in os.environ:
            raise KeyError(
                'ImprovedAgent requires an environment variable called "{}" '
                'pointing to the Stockfish executable'.format(STOCKFISH_ENV_VAR))

        stockfish_path = os.environ[STOCKFISH_ENV_VAR]
        if not os.path.exists(stockfish_path):
            raise ValueError('No stockfish executable found at "{}"'.format(stockfish_path))

        self.engine = chess.engine.SimpleEngine.popen_uci(stockfish_path, setpgrp=True)

   
    # PHASE 1 — PARTICLE FILTER BELIEF STATE
   

    def handle_game_start(self, color: Color, board: chess.Board, opponent_name: str):
        """Seed the candidate set with the single known starting board."""
        self.possible_boards = {board.fen()}
        self.color = color

    def handle_opponent_move_result(self, captured_my_piece: bool, capture_square: Optional[Square]):
        """
        Expand the candidate set by simulating every pseudo-legal opponent move
        on each current candidate board, then filter by the capture observation.

        FIX vs old code:
          - Also includes the null move (opponent might have passed / been forced to).
          - Cap lowered from 10,000 → MAX_BOARDS (500) for speed.
        """
        self.my_piece_captured_square = capture_square
        new_possible_boards = set()

        for board_fen in self.possible_boards:
            board = chess.Board(board_fen)

            # Collect all moves the opponent could have made, including null (no move)
            opponent_moves = list(board.pseudo_legal_moves) + [chess.Move.null()]

            for move in opponent_moves:
                new_board = board.copy()

                if move == chess.Move.null():
                    # Null move: just flip the turn, no pieces move
                    new_board.push(move)
                else:
                    new_board.push(move)

                if captured_my_piece:
                    # Only keep boards where the move landed on the capture square
                    if move != chess.Move.null() and move.to_square == capture_square:
                        new_possible_boards.add(new_board.fen())
                else:
                    # Keep boards where no capture of our piece occurred
                    # (i.e. the move did NOT land on one of our piece squares)
                    if move == chess.Move.null() or move.to_square != capture_square:
                        new_possible_boards.add(new_board.fen())

        # Cap the set — sample randomly if over the limit
        if len(new_possible_boards) > MAX_BOARDS:
            new_possible_boards = set(random.sample(list(new_possible_boards), MAX_BOARDS))

        self.possible_boards = new_possible_boards

    def handle_sense_result(self, sense_result: List[Tuple[Square, Optional[chess.Piece]]]):
        """
        Prune: discard any candidate board whose pieces at the sensed squares
        don't match what was actually observed. This is the most powerful pruning step.
        """
        new_possible_boards = set()

        for board_fen in self.possible_boards:
            board = chess.Board(board_fen)
            consistent = True

            for square, sensed_piece in sense_result:
                if board.piece_at(square) != sensed_piece:
                    consistent = False
                    break

            if consistent:
                new_possible_boards.add(board_fen)

        self.possible_boards = new_possible_boards

    def handle_move_result(self, requested_move: Optional[chess.Move], taken_move: Optional[chess.Move],
                           captured_opponent_piece: bool, capture_square: Optional[Square]):
        """
        Apply our own taken move to every candidate board.
        Boards where that move wasn't pseudo-legal are discarded.
        """
        if taken_move is not None:
            updated_boards = set()

            for board_fen in self.possible_boards:
                board = chess.Board(board_fen)
                if taken_move in board.pseudo_legal_moves:
                    new_board = board.copy()
                    new_board.push(taken_move)
                    updated_boards.add(new_board.fen())

            self.possible_boards = updated_boards

    # PHASE 2 — UNCERTAINTY-BASED SENSE SELECTION
    

    def _square_uncertainty(self) -> dict:
        """
        For each of the 64 squares, compute the fraction of candidate boards
        that have ANY piece on that square.

        Uncertainty is highest at 0.5 (half the boards have a piece, half don't).
        We use the entropy-like formula: u = 1 - |2p - 1|
        which equals 1.0 when p=0.5 and 0.0 when p=0 or p=1.
        """
        if not self.possible_boards:
            return {sq: 0.0 for sq in chess.SQUARES}

        piece_counts = defaultdict(int)
        n = len(self.possible_boards)

        for board_fen in self.possible_boards:
            board = chess.Board(board_fen)
            for square in chess.SQUARES:
                if board.piece_at(square) is not None:
                    piece_counts[square] += 1

        uncertainty = {}
        for square in chess.SQUARES:
            p = piece_counts[square] / n          # fraction of boards with a piece here
            uncertainty[square] = 1.0 - abs(2 * p - 1)   # 0→certain empty, 1→maximally uncertain
        return uncertainty

    def _score_sense_square(self, center_square: int, uncertainty: dict) -> float:
        """
        Score a sense square by averaging the uncertainty of all squares
        in the 3×3 window centred on it.
        """
        file = chess.square_file(center_square)
        rank = chess.square_rank(center_square)
        total = 0.0
        count = 0

        for df in [-1, 0, 1]:
            for dr in [-1, 0, 1]:
                f, r = file + df, rank + dr
                if 0 <= f <= 7 and 0 <= r <= 7:
                    sq = chess.square(f, r)
                    total += uncertainty[sq]
                    count += 1

        return total / count if count > 0 else 0.0

    def choose_sense(self, sense_actions: List[Square], move_actions: List[chess.Move],
                     seconds_left: float) -> Optional[Square]:
        """
        Phase 2: pick the sense square that maximises average uncertainty
        across its 3×3 window.

        Falls back to a random interior square if the candidate set is empty.
        Restricts to interior squares (files 1–6, ranks 1–6) so the full
        3×3 window always fits on the board.
        """
        # Restrict to interior squares so the 3x3 window is always fully on-board
        interior = [
            sq for sq in sense_actions
            if 0 < chess.square_file(sq) < 7 and 0 < chess.square_rank(sq) < 7
        ]

        if not interior:
            return random.choice(sense_actions)

        if not self.possible_boards:
            return random.choice(interior)

        # Compute per-square uncertainty from the candidate set
        uncertainty = self._square_uncertainty()

        # Score each candidate sense square
        best_square = max(interior, key=lambda sq: self._score_sense_square(sq, uncertainty))
        return best_square

   
    # PHASE 3 — MULTI-BOARD STOCKFISH VOTING (move selection)
   
    def choose_move(self, move_actions: List[chess.Move], seconds_left: float) -> Optional[chess.Move]:
        """
        Sample up to MAX_BOARDS candidate boards, run Stockfish on each, and
        return the move that gets the most votes.

        King-capture always takes priority: if any board shows the king is
        capturable, that move is voted on immediately without calling Stockfish.
        """
        move_counts = defaultdict(int)

        # Work from a capped sample for speed
        sample = list(self.possible_boards)
        if len(sample) > MAX_BOARDS:
            sample = random.sample(sample, MAX_BOARDS)

        # Time budget per board: never more than 0.5s, scales down with more boards
        time_per_board = min(0.5, 5.0 / max(len(sample), 1))

        for board_fen in sample:
            board = chess.Board(board_fen)
            color = board.turn
            enemy_king_square = board.king(not color)

            if enemy_king_square:
                attackers = board.attackers(color, enemy_king_square)
                if attackers:
                    # King is capturable on this board — vote for that move immediately
                    attacker_square = attackers.pop()
                    king_move = chess.Move(attacker_square, enemy_king_square)
                    if king_move in move_actions:
                        move_counts[king_move] += 1
                    continue  # don't bother asking Stockfish

            # Ask Stockfish for the best move on this board
            try:
                board.turn = color
                board.clear_stack()
                result = self.engine.play(board, chess.engine.Limit(time=time_per_board))
                if result.move in move_actions:
                    move_counts[result.move] += 1
            except chess.engine.EngineTerminatedError:
                print('Stockfish Engine died')
            except chess.engine.EngineError:
                print(f'Stockfish Engine bad state at "{board_fen}"')

        if move_counts:
            max_votes = max(move_counts.values())
            # Among all moves tied at max_votes, pick lexicographically smallest UCI
            best_move = min(
                (m for m in move_counts if move_counts[m] == max_votes),
                key=lambda m: m.uci()
            )
            if best_move in move_actions:
                return best_move

        return random.choice(move_actions) if move_actions else None

    
    # CLEANUP
   
    def handle_game_end(self, winner_color: Optional[Color], win_reason: Optional[WinReason],
                        game_history: GameHistory):
        try:
            self.engine.quit()
        except chess.engine.EngineTerminatedError:
            pass
