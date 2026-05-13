from typing import List, Optional
import chess.engine
import random
from reconchess import *
from reconchess.utilities import without_opponent_pieces, is_illegal_castle
import os
from collections import defaultdict

STOCKFISH_ENV_VAR = 'STOCKFISH_PATH'


class ImprovedAgent(Player):
    """
    TroutBot uses the Stockfish chess engine to choose moves. In order to run TroutBot you'll need to download
    Stockfish from https://stockfishchess.org/download/ and create an environment variable called STOCKFISH_EXECUTABLE
    that is the path to the downloaded Stockfish executable.
    """
    #DONE
    def __init__(self):
        self.possible_boards = set()
        self.color = None
        self.my_piece_captured_square = None

        # make sure stockfish environment variable exists
        if STOCKFISH_ENV_VAR not in os.environ:
            raise KeyError(
                'TroutBot requires an environment variable called "{}" pointing to the Stockfish executable'.format(
                    STOCKFISH_ENV_VAR))

        # make sure there is actually a file
        stockfish_path = os.environ[STOCKFISH_ENV_VAR]
        if not os.path.exists(stockfish_path):
            raise ValueError('No stockfish executable found at "{}"'.format(stockfish_path))

        # initialize the stockfish engine
        self.engine = chess.engine.SimpleEngine.popen_uci(stockfish_path, setpgrp=True)

    #DONE
    def handle_game_start(self, color: Color, board: chess.Board, opponent_name: str):
        self.possible_boards = {board.fen()}
        self.color = color

    #DONE
    def handle_opponent_move_result(self, captured_my_piece: bool, capture_square: Optional[Square]):
        self.my_piece_captured_square = capture_square
        new_possible_boards = set()

        for board_fen in self.possible_boards:
            board = chess.Board(board_fen)
            for move in board.pseudo_legal_moves:
                new_board = board.copy()
                new_board.push(move)

                if captured_my_piece:
                    if move.to_square == capture_square:
                        new_possible_boards.add(new_board.fen())
                else:
                    new_possible_boards.add(new_board.fen())

        if len(new_possible_boards) > 10000:
            new_possible_boards = set(random.sample(list(new_possible_boards), 10000))

        self.possible_boards = new_possible_boards

    #NEEDS IMPROVEMENT : Jordan + Nolwazi
    def choose_sense(self, sense_actions: List[Square], move_actions: List[chess.Move], seconds_left: float) -> \
            Optional[Square]:
        # making sure sense_actions is only from the interior squares
        sense_actions = [square for square in sense_actions if chess.square_file(square) > 0 and chess.square_file(square) < 7 and chess.square_rank(square) > 0 and chess.square_rank(square) < 7]
        original_sense_actions = sense_actions.copy()

        # otherwise, just randomly choose a sense action, but don't sense on a square where our pieces are located
        for board_fen in self.possible_boards:
            board = chess.Board(board_fen)
            for square, piece in board.piece_map().items():
                # if there is a piece of ours on a square, we don't need to sense there, so remove it from the possible sense actions
                if piece.color == self.color and square in sense_actions:
                    sense_actions.remove(square)
        if sense_actions:
            return random.choice(sense_actions)

        return random.choice(original_sense_actions)

    #DONE
    def handle_sense_result(self, sense_result):
        # keep only boards that agree with every square in the sense result
        new_possible_boards = set()

        for board_fen in self.possible_boards:
            board = chess.Board(board_fen)
            matches_sense = True

            for square, sensed_piece in sense_result:
                board_piece = board.piece_at(square)

                if board_piece != sensed_piece:
                    matches_sense = False
                    break

            if matches_sense:
                new_possible_boards.add(board.fen())

        self.possible_boards = new_possible_boards


    #DONE
    def choose_move(self, move_actions: List[chess.Move], seconds_left: float) -> Optional[chess.Move]:
        move_counts = defaultdict(int)  # Using defaultdict for move counting
        if len(self.possible_boards) > 10000:
            self.possible_boards = set(random.sample(list(self.possible_boards), 10000))
        for board_fen in self.possible_boards:
            board = chess.Board(board_fen)
            color = board.turn
            enemy_king_square = board.king(not color)
            
            if enemy_king_square:
                # If the enemy king is under attack, check for attackers
                enemy_king_attackers = board.attackers(color, enemy_king_square)
                if enemy_king_attackers:
                    # If there are attackers, add the move to the counts
                    attacker_square = enemy_king_attackers.pop()
                    king_capture_move = chess.Move(attacker_square, enemy_king_square)
                    if king_capture_move in move_actions:
                        move_counts[king_capture_move] += 1
                else:
                    # Otherwise, ask Stockfish for a move
                    try:
                        board.turn = color
                        board.clear_stack()
                        time = 10/len(self.possible_boards)  # Allocate time based on the number of possible boards
                        result = self.engine.play(board, chess.engine.Limit(time=time)) 
                        # Only count the move if it's in the list of legal move actions
                        if result.move in move_actions:
                            move_counts[result.move] += 1
                    except chess.engine.EngineTerminatedError:
                        print('Stockfish Engine died')
                    except chess.engine.EngineError:
                        print(f'Stockfish Engine bad state at "{board.fen()}"')

        # If there are moves, return the most common one
        if move_counts:
            # After all moves are considered, find the one with the highest count
            max_count = max(move_counts.values())
            most_common_move = min((move for move in move_counts if move_counts[move] == max_count), key=lambda m: m.uci())  # Get the lexicographically smallest move among those with the highest count)
            if most_common_move in move_actions:
                return most_common_move

        return random.choice(move_actions) if move_actions else None

    #DONE
    def handle_move_result(self, requested_move: Optional[chess.Move], taken_move: Optional[chess.Move],
                           captured_opponent_piece: bool, capture_square: Optional[Square]):
        # if a move was executed, apply it to our board
        if taken_move is not None:
            updated_boards = set()

            for board_fen in self.possible_boards:
                board = chess.Board(board_fen)

                if taken_move in board.pseudo_legal_moves:
                    new_board = board.copy()
                    new_board.push(taken_move)
                    updated_boards.add(new_board.fen())

            self.possible_boards = updated_boards
    #DONE
    def handle_game_end(self, winner_color: Optional[Color], win_reason: Optional[WinReason],
                        game_history: GameHistory):
        try:
            # if the engine is already terminated then this call will throw an exception
            self.engine.quit()
        except chess.engine.EngineTerminatedError:
            pass