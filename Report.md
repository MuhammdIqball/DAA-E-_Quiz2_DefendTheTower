--------------------------------------------------------------------------------
Laporan Proyek Quiz 2 DAA: The Dijkstra Bottleneck Puzzle
Mata Kuliah: Desain & Analisis Algoritma (EF234405)
Anggota Kelompok:
[Nama Anggota 1] — [NRP]
[Nama Anggota 2] — [NRP]
[Nama Anggota 3] — [NRP]

--------------------------------------------------------------------------------
Pernyataan Integritas Akademik
“Dengan nama Allah (Tuhan) Yang Maha Kuasa, saya berjanji dan menyatakan bahwa saya telah menyelesaikan Quiz 2 secara mandiri. Saya tidak terlibat dalam kecurangan, plagiarisme, atau menerima bantuan yang tidak sah dalam bentuk apa pun. Saya lebih lanjut menyatakan bahwa penggunaan alat AI apa pun terbatas pada peran pendukung (seperti untuk pemeriksaan tata bahasa atau debugging), dan bahwa solusi akhir adalah produk dari upaya intelektual saya sendiri. Saya memahami bahwa saya akan menerima semua konsekuensi jika saya terbukti melanggar janji integritas akademik ini.”
Kontribusi Anggota:
[Nama 1] — 33.33%: Implementasi algoritma Dijkstra dan BFS, serta logika validasi graf di pathfinding.py
.
[Nama 2] — 33.33%: Pengembangan arsitektur modular, sistem state machine, dan desain level puzzle mengecoh di levels.py
.
[Nama 3] — 33.33%: Pengembangan antarmuka (UI), sistem inventaris, pengujian performa, dan penyusunan laporan evaluasi teknis
.

--------------------------------------------------------------------------------
1. Design (Desain)
Proyek ini bertransformasi dari prototipe Tower Defense tradisional menjadi sebuah game puzzle logika graf bernama "The Dijkstra Bottleneck Puzzle"
. Fokus utama desain adalah visualisasi teori graf melalui identifikasi bottleneck (titik kritis) di mana pemain harus memutus semua jalur dari Spawn (Source) ke Base (Sink) menggunakan blok terbatas
.
Arsitektur Modular: Perangkat lunak dibagi menjadi lima modul utama untuk memisahkan logika UI dengan mesin pencarian jalur: main.py (state machine), pathfinding.py (algoritma), ui.py (interface), entities.py (objek inventaris), dan levels.py (registry level)
.
Teori Graf dalam Level: Desain level menerapkan prinsip Max-Flow Min-Cut Theorem
.
Level 2 (The False Shortcut): Menggunakan desain dekoratif untuk mengecoh pemain agar memblokir jalur yang terlihat pendek, padahal terdapat jalur konvergensi di titik (12,7) yang harus diputus
.
Level 3 (The Spider Web): Implementasi langsung dari node-disjoint paths, di mana pemain harus menemukan Minimum Cut sebesar 2 untuk memutus total hubungan graf yang menyerupai jaring laba-laba
.
2. Implementation (Implementasi)
Implementasi dilakukan menggunakan bahasa pemrograman Python dan library Pygame
. Sistem menggunakan dua algoritma graf untuk tujuan yang berbeda (Algorithmic Dualism)
:
Breadth-First Search (BFS): Diimplementasikan dengan collections.deque untuk memberikan preview jalur terpendek secara real-time saat pemain melakukan aksi drag-to-build
. Kompleksitasnya adalah O(V+E), menjamin performa responsif pada grid 20x15
.
Dijkstra’s Algorithm: Digunakan sebagai validator solusi akhir saat pemain menekan "Submit"
. Implementasi ini menggunakan min-priority queue melalui library heapq Python untuk memenuhi persyaratan akademik Quiz 2
. Kompleksitasnya adalah O((V+E)logV)
.
Representasi Grid: Grid dikelola sebagai matriks 2D di mana nilai sel menentukan sifatnya: 0 untuk area bisa dilewati, 1 untuk rintangan/tembok, dan 2 untuk No-Build Zone (rawa) yang bisa dilewati musuh namun tidak bisa dibangun oleh pemain
.
3. Evaluation (Evaluasi)
Evaluasi dilakukan melalui analisis empiris terhadap waktu eksekusi algoritma Dijkstra pada berbagai topologi level menggunakan modul time
.
Dijkstra vs. BFS: Pada grid 20x15 (300 node), BFS melakukan ~300 operasi sementara Dijkstra melakukan ~2.400 operasi (300⋅log300)
. Meskipun overhead Dijkstra lebih besar, waktu eksekusinya tetap di bawah ambang batas persepsi manusia, menjadikannya validator yang kokoh
.
Dampak Kepadatan Obstacle: Ditemukan sebuah paradoks di Level 2 (False Shortcut); meskipun secara visual rumit dengan 108 rintangan permanen, level ini menunjukkan performa eksekusi tercepat
. Hal ini dikarenakan rintangan tersebut melakukan pruning terhadap ruang pencarian (mengurangi jumlah edge aktif), sehingga mempercepat algoritma mencapai konklusi
.
Kompleksitas Level 3: Tingkat kesulitan tertinggi ditemukan pada "The Spider Web" karena rasio edge-to-node yang tinggi, memaksa algoritma mengeksplorasi lebih banyak jalur sebelum memastikan graf terputus sepenuhnya
.
4. Conclusion (Kesimpulan)
Proyek "The Dijkstra Bottleneck Puzzle" berhasil memenuhi seluruh kriteria Quiz 2 DAA melalui implementasi algoritma Dijkstra berbasis priority queue dan BFS
. Transisi dari game aksi ke puzzle logika memperkuat nilai edukasi proyek dalam menjelaskan konsep konektivitas graf, minimum cut, dan efisiensi algoritma
. Integrasi arsitektur modular memungkinkan pengembangan sistem yang performan sekaligus teoritis, memberikan simulasi yang akurat tentang bagaimana hambatan lingkungan mempengaruhi pencarian jalur secara komputasi
.

--------------------------------------------------------------------------------
GitHub Repository: [Public Link Anda Disini]