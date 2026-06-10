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

```

## Penjelasan Program

Program Client:

`main_client.py`:

Code ini berfungsi menghubungkan input pemain, koneksi ke server, dan juga interface game di modul lainnya. Di awal kode, program mengaktifkan logging dengan format sederhana supaya status koneksi, error, dan info runtime mudah dibaca. Program lalu menjalankan fungsi `start_client()` yang berisi:
1. Client diminta username dari terminal dengan input. Jika username dikosongkan, program membuat nama otomatis dengan pola Player_ lalu ditambah nilai waktu dari `pygame.time.get_ticks()`.
2. Setelah itu dibuat objek `NetworkClient` dengan player_id tadi Client mencoba connect ke server pada alamat dan port yang diambil dari `shared/config.py`. Jika koneksi berhasil, program mencatat bahwa server tersambung dan lanjut membuka arena game. Jika koneksi gagal, arena tetap dibuka, lalu mekanisme reconnect otomatis akan dijalankan oleh `NetworkClient`.
3. Saat arena sudah siap, fungsi `run_game()` dipanggil untuk menjalankan loop visual dan gameplay. Jika server tidak aktif, `ConnectionRefusedError` ditangani secara khusus supaya pesan yang muncul lebih jelas. Error lain ditangani oleh blok Exception umum.
4. Di bagian finally, koneksi network ditutup agar socket tidak dibiarkan terbuka.

Jadi, `main_client.py` berfungsi sebagai pintu masuk client yang mengatur alur dari input username, koneksi ke server, hingga menjalankan game di arena.

<br>

`network_client.py`:

Code ini berfungsi sebagai penghubung komunikasi antara client dan server, sekaligus penyimpan state game di sisi client. Di dalam kode ini ada class `NetworkClient` yang mengatur socket, thread penerima data, thread ping, dan mekanisme reconnect otomatis. Alur kerjanya sebagai berikut:
1. Saat objek `NetworkClient` dibuat, program menyimpan `player_id`, menyiapkan socket, lock, flag kontrol koneksi, dan dictionary `game_state` untuk menyimpan data pemain, map, ping, status game, dan informasi lobby.
2. Method `connect()` dipakai untuk membuka koneksi ke server menggunakan IP dan Port dari `shared/config.py`. Jika koneksi berhasil, client langsung mengirim packet `join` berisi `player_id`, lalu menjalankan thread `receive_loop` untuk menerima data dari server dan thread `ping_loop` untuk mengecek latensi koneksi.
3. Method `send()` dipakai untuk mengirim data ke server. Data yang dikirim diubah dulu menjadi packet JSON melalui fungsi `encode_packet()` dari `shared/packet_parser.py`, lalu dikirim melalui socket. Jika pengiriman gagal, koneksi dianggap putus dan client akan menandai status reconnect.
4. Method `_receive_loop()` terus membaca data dari socket, menampungnya di buffer, lalu memecahnya menjadi packet utuh memakai `decode_stream()`. Setiap packet yang masuk akan diteruskan ke `_handle_packet()` untuk memperbarui `game_state`.
5. Method `_handle_packet()` adalah bagian penting karena di sinilah respon dari server diproses. `sync_players` memperbarui data client, `sync_map` memperbarui map, `pong` dipakai untuk menghitung ping, `join_ack` menyimpan status join atau reconnect, `game_start` dan `game_over` mengubah status game, sedangkan `lobby_state` menyimpan jumlah client di lobby.
6. Jika koneksi terputus, method `_mark_disconnected()` menutup socket lama dan mengubah status menjadi reconnecting. Setelah itu `_schedule_reconnect()` akan menjalankan `_reconnect_loop()` yang terus mencoba reconnect hingga berhasil atau program ditutup.
7. Method `_ping_loop()` secara berkala mengirim packet `ping` ke server. Packet ini dibalas server dengan `pong`, lalu selisih waktunya dipakai untuk menghitung nilai ping yang ditampilkan di display game.
8. Method `close()` dipanggil saat client selesai agar koneksi dihentikan dengan rapi dan socket ditutup.

Jadi, `network_client.py` bertugas menyambungkan client ke server, menjaga koneksi tetap hidup, menyimpan state terbaru game, dan memastikan client bisa pulih otomatis jika koneksi terputus.

<br>

`arena.py`:

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


## Screenshot Hasil
