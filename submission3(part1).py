import chess
import chess.engine
engine = chess.engine.SimpleEngine.popen_uci('/opt/stockfish/stockfish', setpgrp=True)

fen= input().strip()         # Read FEN string input and remove any whitespaces/tabs from string from beginning to end
board = chess.Board(fen)     # Convert FEN string into a Chess board

def choose_move(board):
        # if we might be able to take the king, try to
        color = board.turn
        enemy_king_square = board.king(not color)
        if enemy_king_square:
            # if there are any ally pieces that can take king, execute one of those moves
            enemy_king_attackers = board.attackers(color, enemy_king_square)
            if enemy_king_attackers:
                attacker_square = enemy_king_attackers.pop()
                print(chess.Move(attacker_square, enemy_king_square))
        # otherwise, try to move with the stockfish chess 
            else:
                try:
                    board.turn = color
                    board.clear_stack()
                    result = engine.play(board, chess.engine.Limit(time=0.5))
                    print(result.move)
                except chess.engine.EngineTerminatedError:
                    print('Stockfish Engine died')
                except chess.engine.EngineError:
                    print('Stockfish Engine bad state at "{}"'.format(board.fen()))

        # if all else fails, pass
        return None

choose_move(board)

engine.quit()