class RoomState:
    def __init__(self):
        self.doors = {
            "door_main": {"required_energy": 50},
            "door_left": {"required_energy": 100},
            "door_right": {"required_energy": 200},
            "door_top": {"required_energy": 500},
            "door_sec1": {"required_energy": 150},
            "door_sec2": {"required_energy": 300}
        }
        
        self.terminals = {
            "term_tut": {
                "reward": 50,
                "question": "Protokol remote connection versi lama yang sudah tidak aman dan digantikan oleh SSH?", 
                "flag": "telnet"
            },
            "term_e1": {
                "reward": 50,
                "question": "Konstanta tipe socket pada Python yang digunakan untuk protokol TCP?", 
                "flag": "sock_stream"
            },
            "term_e2": {
                "reward": 50,
                "question": "Port default yang digunakan oleh protokol SMTP untuk mengirim email?", 
                "flag": "25"
            },
            "term_e3": {
                "reward": 50,
                "question": "Method pada socket TCP server yang bersifat blocking untuk menunggu klien terkoneksi?", 
                "flag": "accept"
            },
            "term_m1": {
                "reward": 100,
                "question": "Konstanta tipe socket pada Python yang digunakan untuk protokol UDP?", 
                "flag": "sock_dgram"
            },
            "term_m2": {
                "reward": 100,
                "question": "Nama library bawaan Python untuk mengimplementasikan FTP client?", 
                "flag": "ftplib"
            },
            "term_m3": {
                "reward": 100,
                "question": "Protokol manajemen email tersentralisasi yang diciptakan oleh Mark R. Crispin pada 1986?", 
                "flag": "imap"
            },
            "term_h1": {
                "reward": 200,
                "question": "Modul Python untuk I/O Multiplexing guna memonitor banyak socket sekaligus tanpa threading?", 
                "flag": "select"
            },
            "term_h2": {
                "reward": 200,
                "question": "Ilmuwan komputer asal CMU yang menciptakan istilah Remote Procedure Call (RPC) pada tahun 1981?", 
                "flag": "bruce jay nelson"
            },
            "term_h3": {
                "reward": 300,
                "question": "Library/algoritma kompresi yang dicontohkan pada materi object serialization untuk menghemat bandwidth?", 
                "flag": "zlib"
            },
            "term_sec1": {
                "reward": 150,
                "question": "Tokoh penting di ARPANET yang menstandarisasi protokol UDP (RFC 768) dan SMTP (RFC 772)?", 
                "flag": "jon postel"
            },
            "term_sec2": {
                "reward": 250,
                "question": "Tool pembuka secure tunnel untuk mengekspos local server ke internet tanpa perlu konfigurasi NAT/Router?", 
                "flag": "ngrok"
            }
        }

    def get_full_state(self):
        safe_terminals = {}
        for t_id, t_data in self.terminals.items():
            safe_terminals[t_id] = {
                "reward": t_data.get("reward", 0),
                "question": t_data.get("question", "Soal belum tersedia.")
            }
            
        return {
            "doors": self.doors,
            "terminals": safe_terminals
        }