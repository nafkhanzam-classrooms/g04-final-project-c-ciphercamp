import logging
import pygame
from client.network_client import NetworkClient
from client.arena import run_game 
from shared.config import SERVER_IP, SERVER_PORT

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

def start_client():
    player_id = input("Masukkan username kamu: ").strip()
    if not player_id:
        player_id = "Player_" + str(int(pygame.time.get_ticks() / 1000))

    net_client = NetworkClient(player_id)
    logging.info(f"Mencoba connect ke {SERVER_IP}:{SERVER_PORT}...")
    
    try:
        if net_client.connect():
            logging.info("Tersambung ke server. Memulai Arena...")
        else:
            logging.warning("Belum tersambung ke server. Arena tetap dibuka dan akan mencoba reconnect otomatis.")
        run_game(player_id, net_client)
        
    except ConnectionRefusedError:
        logging.error("Server tidak ditemukan! Pastikan main_server.py menyala.")
    except Exception as e:
        logging.error(f"Error kritis: {e}")
    finally:
        try:
            net_client.close()
            logging.info("Koneksi jaringan ditutup.")
        except Exception:
            pass

if __name__ == "__main__":
    start_client()