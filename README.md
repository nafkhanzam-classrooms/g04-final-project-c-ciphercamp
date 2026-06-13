[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/90Mprfp5)
# Network Programming - Final Project [G04]

## Anggota Kelompok
| Nama                        | NRP        | Kelas                    |
| ---                         | ---        | ----------               |
| Puspita Wijayanti Kusuma    | 5025241059 | Pemrograman Jaringan C   |
| Christina Tan               | 5025241060 | Pemrograman Jaringan C   |
| Athar Bakhtiar Aziz         | 5025241136 | Pemrograman Jaringan C   |

## Link Youtube (Unlisted)
Link ditaruh di bawah ini
```
https://youtu.be/iErkBj4HysM
```

## Penjelasan Program

### Program Client:

#### `main_client.py`:

Code ini berfungsi menghubungkan input pemain, koneksi ke server, dan juga interface game di modul lainnya. Di awal kode, program mengaktifkan logging dengan format sederhana supaya status koneksi, error, dan info runtime mudah dibaca. Program lalu menjalankan fungsi `start_client()` yang berisi:
1. Client diminta memasukkan username dari terminal. Jika username dikosongkan, program membuat nama otomatis dengan pola `Player_` lalu ditambah nilai waktu dari `pygame.time.get_ticks()`.
2. Setelah itu dibuat objek `NetworkClient` dengan `player_id` tadi. Program lalu mencoba mencari server secara otomatis di jaringan LAN/hotspot yang sama melalui `discover_server()`. Jika server tidak ditemukan, client meminta input IP dan port secara manual, dengan fallback ke nilai default dari `shared/config.py`.
3. Setelah `NetworkClient` siap, program mencoba `connect()` ke server. Jika koneksi berhasil, program mencatat bahwa server tersambung. Jika gagal, program hanya memberi peringatan dan tetap membuka arena agar client bisa mencoba reconnect otomatis. Setelah itu `run_game()` dipanggil untuk menjalankan loop visual dan gameplay. `ConnectionRefusedError` ditangani secara khusus supaya pesan yang muncul lebih jelas, sedangkan error lain ditangani oleh blok `Exception` umum.
4. Di bagian `finally`, koneksi network ditutup agar socket tidak dibiarkan terbuka.

Jadi, `main_client.py` berfungsi sebagai pintu masuk client yang mengatur alur dari input username, koneksi ke server, hingga menjalankan game di arena.

<br>

#### `network_client.py`:

Code ini berfungsi sebagai penghubung komunikasi antara client dan server, sekaligus penyimpan state game di sisi client. Di dalam kode ini ada class `NetworkClient` yang mengatur socket, thread penerima data, thread ping, dan mekanisme reconnect otomatis. Alur kerjanya sebagai berikut:
1. Saat objek `NetworkClient` dibuat, program menyimpan `player_id`, `server_ip`, dan `server_port`, lalu menyiapkan socket, lock, flag kontrol koneksi, dan dictionary `game_state` untuk menyimpan data pemain, map, ping, status koneksi, status game, dan informasi lobby.
2. Di luar class `NetworkClient`, ada fungsi `discover_server()` yang dipakai untuk mencari server secara otomatis lewat UDP broadcast. Fungsi ini akan mengembalikan IP dan port server jika ditemukan, atau `None` jika tidak ada respons.
3. Method `connect()` dipakai untuk membuka koneksi ke server menggunakan `server_ip` dan `server_port` yang sudah disimpan di objek. Jika koneksi berhasil, client langsung mengirim packet `join` berisi `player_id`, lalu menjalankan thread `_receive_loop()` untuk menerima data dari server dan thread `_ping_loop()` untuk mengecek latensi koneksi.
4. Method `send()` dipakai untuk mengirim data ke server. Data yang dikirim diubah dulu menjadi packet JSON melalui fungsi `encode_packet()` dari `shared/packet_parser.py`, lalu dikirim melalui socket. Jika pengiriman gagal, koneksi dianggap putus dan client menandai status menjadi reconnecting.
5. Method `_receive_loop()` terus membaca data dari socket, menampungnya di buffer, lalu memecahnya menjadi packet utuh memakai `decode_stream()`. Setiap packet yang masuk akan diteruskan ke `_handle_packet()` untuk memperbarui `game_state`.
6. Method `_handle_packet()` memproses respon dari server. `sync_players` memperbarui data pemain, `sync_map` memperbarui map, `pong` dipakai untuk menghitung ping, `join_ack` menyimpan status join atau reconnect sekaligus info lobby, `game_start` dan `game_over` mengubah status game, `notify` menambahkan notifikasi, sedangkan `lobby_state` menyimpan jumlah client di lobby.
7. Jika koneksi terputus, method `_mark_disconnected()` menutup socket lama dan mengubah status menjadi reconnecting. Setelah itu `_schedule_reconnect()` akan menjalankan `_reconnect_loop()` yang terus mencoba reconnect hingga berhasil atau program ditutup.
8. Method `_ping_loop()` secara berkala mengirim packet `ping` ke server setiap 2 detik. Packet ini dibalas server dengan `pong`, lalu selisih waktunya dipakai untuk menghitung nilai ping yang disimpan di `game_state`.
9. Method `close()` dipanggil saat client selesai agar koneksi dihentikan dengan rapi dan socket ditutup.

Jadi, `network_client.py` bertugas menyambungkan client ke server, menjaga koneksi tetap hidup, menyimpan state terbaru game, dan memastikan client bisa pulih otomatis jika koneksi terputus.

<br>

#### `arena.py`:

Code ini berfungsi sebagai tampilan utama game di sisi client, yaitu tempat semua elemen visual, input pemain, dan interaksi gameplay digabungkan. Di dalam file ini, fungsi `run_game()` menjalankan loop utama Pygame, menggambar map, menampilkan pemain, memproses input keyboard, serta membaca state terbaru dari `NetworkClient`. Alur kerjanya sebagai berikut:
1. Di awal program, `arena.py` menyiapkan helper seperti `rect_from_data()` untuk mengubah data koordinat dari server menjadi `pygame.Rect`, `get_spawn_position()` untuk menentukan titik spawn player, serta `get_sprites_for_asset()` untuk memuat sprite player dari folder `assets/player{n}` dan menyimpannya ke cache agar tidak dimuat berulang.
2. Fungsi `get_ranked_players()` dan `draw_live_leaderboard()` dipakai untuk membuat leaderboard live di layar. Data pemain diurutkan berdasarkan poin, lalu ditampilkan dengan posisi, nama, poin, dan status online/offline.
3. Saat `run_game()` dipanggil, program membuat window Pygame, mengatur caption game, menyiapkan clock, dan memuat font untuk tampilan game, tooltip, serta soal game. Setelah itu Pygame diinisialisasi dan sprite default dicoba untuk diload lebih dulu.
4. Di dalam fungsi ini juga dibangun layout map lokal sebagai fallback, seperti daftar `rooms`, `door_rects`, `connection_rects`, `walls`, dan `terminal_rects`. Namun jika server mengirim state map terbaru, client akan memakai data dari server agar tampilan tetap sinkron.
5. Setiap frame, program membaca `net_client.game_state` untuk mengambil `map_state`, `players`, status lobby, status game, ping, dan informasi lain. Dari data itu, `arena.py` menentukan posisi room, wall, pintu, terminal, dan pemain yang harus digambar.
6. Bagian input keyboard diproses di event loop. Tombol `WASD` dipakai untuk bergerak, `E` dipakai untuk interaksi, `Enter` untuk submit jawaban, dan `Escape` untuk membatalkan. Saat pemain bergerak, client mengecek collision dengan wall dan pintu tertutup sebelum mengirim aksi `move` ke server.
7. Jika pemain berada dekat terminal lalu menekan `E`, game masuk ke `hacking_mode` dan menampilkan overlay soal. Saat player memasukkan jawaban lalu menekan `Enter`, client mengirim packet `submit_flag` ke server. Jika client di dekat pintu dan menekan `E`, client mengirim aksi `open_door`.
8. Pada bagian rendering, `arena.py` menggambar room, wall, terminal, pintu, pemain lain, energy/poin/ping, status reconnect, leaderboard, timer game, dan overlay soal. Jika server mengirim status `game_over`, layar menampilkan daftar leaderboard akhir dan menunggu pemain keluar.

Jadi, `arena.py` berfungsi mengubah data game dari server menjadi tampilan interaktif yang bisa dimainkan, sekaligus menjadi tempat utama input dan visualisasi gameplay di sisi client.

### Program Server:

#### `main_server.py`:
File `main_server.py` berperan sebagai pintu masuk untuk memulaikan program Server.

Kode ini dimulai dengan menginisialisasi logging.

Setelah logging di-inisialisasi, 
1. Program server meminta untuk memasukkan jumlah player maksimum yang akan bergabung, dimana jumlah player tersebut dibataskan dari 2 sampai 4. Jumlah player tersebut akan disimpan dalam `max_players`. Jika terjadi Exception saat melakukan input, `max_players` diatur menjadi 4. Jika input kurang dari 2, `max_players` diatur menjadi 2, dan jika input lebih dari 4, `max_players` diatur menjadi 4.
2. Program membuat objek `NetworkHandler` bernama `server` yang akan menangani networking.
3. Program membuat objek `GameLogic` bernama `game` yang akan menangani logika game.
4. Callback `process_action` pada `server` diatur menjadi fungsi `game.process_action` dan callback `on_disconnect` pada `server` diatur menjadi `game.remove_player`
5. Server dimulai dengan menjalankan `server.start`. Jika terjadi exception `KeyboardInterrupt`, server akan berhenti dengan informasi log berisi "Server dimatikan secara manual.".

#### `network_handler.py`:

File `network_handler.py` mencakup class:
``` python
class NetworkHandler:
```
Class `NetworkHandler` berfungsi untuk menangani networking antar server dengan client. Tugas dari `NetworkHandler` mencakup penanganan client, pembersihan client, pengiriman data ke client, dan broadcast, yaitu pengiriman data ke seluruh client.

Konstruktor `NetworkHandler` adalah:
``` python
    def __init__(self, game_logic_callback, host='0.0.0.0', port=5555, max_players=4):
```
`game_logic_callback` berisi callback untuk memproses aksi client. Argumen untuk callback `game_logic_callback`berupa `(cid, data)`, dengan `cid` sebagai id client dan `data` sebagai data yang akan diproses. `host` dan `port` digunakan untuk menentukan host dan port yang digunakan server, dan `max_players` menentukan jumlah player yang dapat bergabung.

Atribut-atribut dari class `NetworkHandler` adalah sebagai berikut: 
``` python
self.host = host
self.port = port
self.max_players = max_players
self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

self.clients = {}
self.lock = threading.Lock()

self.process_action = game_logic_callback
self.on_disconnect = None
```

`NetworkHandler` dimulai melalui method:
``` python
def start(self):
```
Isi method `start` ditaruh dalam `try` block. 

Dalam bagian `try`, kode dimulai dengan melakukan `bind` di `server_socket` dengan address `(host, port)`. `server_socket` kemudian dimasukkan ke mode *listening*. 

Setelah dalam mode *listening*, kode memasuki loop `while True`, dimana `server_socket` akan menerima koneksi client, kemudian `client_socket` dan `addr` dari menerima client akan digunakan untuk membuat thread baru `client_thread`, yang menggunakan `handle_client` sebagai target dan `client_socket` dan `addr` sebagai argumen dari target tersebut. Agar `client_thread` tidak memblokir saat program server ditutup, atribut `daemon` di `client_thread` diatur menjadi `True`.

Dalam bagian `except`, logging error dilakukan dengan format f"Gagal memulai server: {e}", dimana e adalah `Exception` yang ditangkap.

Dalam bagian `finally`, `server_socket` ditutup.


Penanganan client dilakukan melalui method:
```python
def handle_client(self, client_socket, addr):
```
Pada awal kode `handle_client`, dibuat variabel berikut:
``` python
client_id = None
buffer = ""
```
Kode kemudian memasuki `try` block, dimana terdapat loop `while True`.

Dalam loop `while True` tersebut, program membaca data `client_socket` dengan `.recv()` dan menaruhnya dalam variabel `data`. `buffer` kemudian ditambah dengan `data` yang di-decode dengan `utf-8` sebagai encodingnya.

#### `room_state.py`:



#### `game_logic.py`:

#### `player_session.py`:     
File ini Berfungsi untuk menyimpan struktur data pemain pada sisi server. Di dalam file ini terdapat class:

```python
class PlayerSession:
```

Class `PlayerSession` digunakan untuk merepresentasikan satu player yang sedang bermain. Setiap player memiliki data seperti ID player, posisi, arah gerak, poin, energi, aset karakter, status koneksi, serta progress permainan.

Pada constructor, data player dibuat melalui:

```python
def __init__(self, player_id, start_x=480, start_y=580, asset_index: int = 1):
```

Parameter `player_id` digunakan sebagai identitas pemain. Sementara itu, `start_x` dan `start_y` digunakan sebagai posisi awal player. Atribut `asset_index` digunakan untuk menentukan tampilan karakter yang dipakai player.

Beberapa atribut utama yang disimpan adalah:

```python
self.player_id = player_id
self.x = start_x
self.y = start_y
self.dir = "down"
self.points = 0
self.energy = 200
self.asset = asset_index
```

Atribut tersebut menunjukkan bahwa setiap player memiliki posisi koordinat, arah hadap, jumlah poin, energi, dan karakter yang digunakan.

File ini juga menyimpan status koneksi player:

```python
self.connected = True
self.disconnected_at = None
```

Atribut `connected` digunakan untuk menandai apakah player sedang terhubung ke server atau tidak. Atribut `disconnected_at` digunakan untuk menyimpan waktu ketika player terputus dari server.

Bagian ini mendukung fitur **reconnect handling**. Ketika player disconnect, server tidak langsung menghapus data player. Server cukup mengubah status koneksi player melalui method:

```python
def mark_disconnected(self, disconnected_at):
    self.connected = False
    self.disconnected_at = disconnected_at
```

Jika player masuk kembali dengan username yang sama, server dapat mengaktifkan kembali session tersebut menggunakan:

```python
def mark_connected(self):
    self.connected = True
    self.disconnected_at = None
```

Dengan cara ini, player dapat melanjutkan permainan tanpa harus mulai dari awal.

Selain data posisi dan koneksi, file ini juga menyimpan progress permainan player. Progress pintu disimpan dalam:

```python
self.door_open_state
```

Sedangkan progress terminal disimpan dalam:

```python
self.terminal_solve_state
```

Data ini digunakan untuk mengetahui pintu mana yang sudah terbuka dan terminal mana yang sudah berhasil diselesaikan oleh player.

Agar data player dapat dikirim ke client, class ini memiliki method:

```python
def to_dict(self):
```

Method `to_dict()` mengubah objek `PlayerSession` menjadi dictionary. Data ini kemudian dapat dikirim oleh server ke client dalam pesan sinkronisasi, misalnya melalui pesan `sync_players`.

<br>


### Program Shared:
#### `config.py`:  

File `config.py` berfungsi sebagai file konfigurasi bersama yang digunakan oleh client dan server. Di dalam file ini terdapat pengaturan yang dibutuhkan game, seperti alamat IP server, port server, ukuran layar, FPS, warna objek, dan ukuran tile.

Pada bagian jaringan, terdapat konfigurasi:

```python
SERVER_IP = '127.0.0.1'
SERVER_PORT = 5555
```

Konfigurasi tersebut digunakan oleh client untuk mengetahui alamat server yang akan dihubungi. Karena server berjalan secara lokal, IP yang digunakan adalah `127.0.0.1`, sedangkan port yang digunakan adalah `5555`.

Selain itu, file ini juga menyimpan konfigurasi tampilan game, seperti:

```python
WIDTH, HEIGHT = 1000, 700
FPS = 60
```

Bagian tersebut menentukan ukuran window game dan jumlah frame per second yang digunakan. Dengan adanya konfigurasi ini, tampilan game dapat dibuat konsisten di seluruh bagian program.

File ini juga mendefinisikan beberapa warna yang digunakan untuk objek di dalam game, seperti warna background, dinding, lantai, player, pintu, terminal, dan teks. Contohnya:

```python
PLAYER_ME_COLOR = (100, 255, 100)
PLAYER_OTHER_COLOR = (255, 100, 100)
DOOR_COLOR = (200, 50, 50)
TERMINAL_COLOR = (0, 180, 255)
```

Dengan menyimpan warna dan ukuran dalam satu file, pengaturan game menjadi lebih mudah diubah tanpa harus mencari satu per satu di file client atau server.

Jadi, `config.py` berperan sebagai **pusat konfigurasi bersama** yang menyimpan nilai-nilai tetap yang digunakan dalam game, baik untuk kebutuhan jaringan maupun tampilan permainan.

<br>

#### `packet_parser.py`:  

File `packet_parser.py` berfungsi untuk mengatur format pesan yang dikirim antara client dan server. Game ini menggunakan format pesan berbasis **JSON**. JSON dipilih karena mudah dibaca, mudah diproses di Python, dan cocok untuk mengirim data dalam bentuk pasangan key-value.

Di dalam file ini terdapat fungsi:

```python
def encode_packet(data_dict):
    return json.dumps(data_dict) + "\n"
```

Fungsi `encode_packet()` digunakan untuk mengubah dictionary Python menjadi string JSON. Setelah itu, pesan ditambahkan karakter newline `\n` di bagian akhir. Karakter newline digunakan sebagai penanda akhir dari satu pesan.

Hal ini penting karena komunikasi menggunakan TCP berbentuk stream. Artinya, data yang diterima client atau server belum tentu langsung berupa satu pesan utuh. Oleh karena itu, setiap pesan perlu diberi pemisah agar dapat dibaca dengan benar.

Selain itu, terdapat fungsi:

```python
def decode_stream(buffer):
```

Fungsi `decode_stream()` digunakan untuk membaca data yang masuk dari jaringan. Fungsi ini memecah data berdasarkan newline `\n`, lalu setiap pesan akan diubah kembali dari string JSON menjadi dictionary Python menggunakan `json.loads()`.

Jika pesan yang diterima rusak atau bukan JSON yang valid, maka pesan tersebut tidak diproses dan akan dicatat melalui logging:

```python
logging.warning("Menerima data korup dari stream, membuang packet.")
```

Dengan mekanisme ini, program dapat menghindari error akibat packet yang tidak valid.

Format pesan yang digunakan dalam komunikasi client-server secara umum berbentuk seperti berikut:

```json
{
  "type": "action",
  "action": "move",
  "x": 300,
  "y": 420,
  "dir": "down"
}
```

Setiap pesan memiliki atribut utama `type` untuk menunjukkan jenis pesan. Jika pesan berisi aksi player, maka digunakan tambahan atribut `action`. Contohnya aksi bergerak, membuka pintu, mengirim flag, atau melakukan ping ke server.

Jadi, `packet_parser.py` berperan sebagai **pengatur encoding dan decoding packet** agar komunikasi antara client dan server dapat berjalan rapi, terstruktur, dan tidak tercampur antar pesan.

```main_server.py```

## Screenshot Hasil
