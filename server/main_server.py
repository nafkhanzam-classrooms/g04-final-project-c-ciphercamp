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
    
    server = NetworkHandler(game_logic_callback=lambda cid, data: None, host='0.0.0.0', port=5555)
    
    game = GameLogic(network_handler=server)
    
    server.process_action = game.process_action
    
    try:
        server.start()
    except KeyboardInterrupt:
        logging.info("Server dimatikan secara manual.")