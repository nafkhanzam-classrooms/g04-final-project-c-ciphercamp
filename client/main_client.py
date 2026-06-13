import logging
import pygame
from client.network_client import NetworkClient, discover_server
from client.arena import run_game 
from shared.config import SERVER_IP, SERVER_PORT

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

def start_client():
    player_id = input("Masukkan username kamu: ").strip()
    if not player_id:
        player_id = "Player_" + str(int(pygame.time.get_ticks() / 1000))

    print("\nMencari CipherCamp server otomatis di jaringan LAN/hotspot yang sama...")
    discovered_server = discover_server(timeout=3.0, attempts=3)

    if discovered_server:
        server_ip, server_port = discovered_server
        print(f"Server ditemukan otomatis: {server_ip}:{server_port}")
    else:
        print("Server tidak ditemukan otomatis.")
        print("Fallback: masukkan IP server manual atau kosongkan untuk localhost.")

        server_ip = input("Masukkan IP server (kosongkan untuk localhost): ").strip()
        if not server_ip:
            server_ip = SERVER_IP

        try:
            server_port = int(input(f"Masukkan port server (kosongkan untuk {SERVER_PORT}): ").strip() or SERVER_PORT)
        except ValueError:
            server_port = SERVER_PORT

    net_client = NetworkClient(player_id, server_ip=server_ip, server_port=server_port)
    logging.info(f"Mencoba connect ke {server_ip}:{server_port}...")
    
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
