import logging
import time
from server.network_handler import NetworkHandler
from server.game_logic import GameLogic

logging.Formatter.converter = time.gmtime
logging.basicConfig(
    level=logging.INFO, 
    format='[%(asctime)s UTC] %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

if __name__ == "__main__":
    logging.info("--- Memulai CipherCamp Server ---")
    try:
        max_players = int(input("Masukkan max player (2-4): ").strip() or 4)
    except Exception:
        max_players = 4

    if max_players < 2:
        max_players = 2
    if max_players > 4:
        max_players = 4

    server = NetworkHandler(game_logic_callback=lambda cid, data: None, host='0.0.0.0', port=5555, max_players=max_players)
    
    game = GameLogic(network_handler=server, max_players=max_players)
    
    server.process_action = game.process_action
    server.on_disconnect = game.remove_player
    
    try:
        server.start()
    except KeyboardInterrupt:
        logging.info("Server dimatikan.")