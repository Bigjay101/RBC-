import chess
import chess.engine
from collections import defaultdict

# Open the Stockfish engine
engine = chess.engine.SimpleEngine.popen_uci('/opt/stockfish/stockfish', setpgrp=True)

# Read number of boards
N = int(input().strip())         
board_list = []

# Read FEN strings and append to board_list
for _ in range(N):
    fen = input().strip()         
    board = chess.Board(fen)     
    board_list.append(board)     

def choose_move(board_list):
    move_counts = defaultdict(int)  # Using defaultdict for move counting
    for board in board_list:
        color = board.turn
        enemy_king_square = board.king(not color)
        
        if enemy_king_square:
            # If the enemy king is under attack, check for attackers
            enemy_king_attackers = board.attackers(color, enemy_king_square)
            
            if enemy_king_attackers:
                # If there are attackers, add the move to the counts
                attacker_square = enemy_king_attackers.pop()
                move_counts[chess.Move(attacker_square, enemy_king_square)] += 1
            else:
                # Otherwise, ask Stockfish for a move
                try:
                    board.turn = color
                    board.clear_stack()
                    result = engine.play(board, chess.engine.Limit(time=0.05))  # Reduced time limit to 0.05s
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
        return most_common_move
    return None

# Get the best move for the given board list
chosen_move = choose_move(board_list)

if chosen_move:
    print(chosen_move)

# Close the Stockfish engine
engine.quit()