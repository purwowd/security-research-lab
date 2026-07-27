# Study Case Interview — Magang Cyber (Offensive / Defensive)

**Untuk**: interviewer (kamu)  
**Kandidat**: Raffael Rajjah Wellas Dwyyana (RRWD) — lihat `RRWD CV.pdf`  
**Level**: magang — tidak terlalu berat, tapi tricky & menguras otak  
**Fokus**: development offensive/defensive, crypto, coding, riset tanpa referensi  
**Cara pakai**: pilih 6–8 soal (mix kategori). Jangan habisin semua — 45–60 menit cukup.

### Brief CV (buat ngepasin soal)

| Area | Yang dia klaim |
|------|----------------|
| Crypto project (Toulouse, 2024) | CLI C: encrypt/decrypt, **XOR**, **CBC + IV**, **Diffie-Hellman** simulator, key management, “cryptanalysis” |
| Coding | Java/C# OOP, Python scripting, **C low-level**, Git, Linux |
| Background | CS Toulouse III; SMK Telkom (telecommunication access network) |
| Gap yang perlu diuji | Klaim crypto agak “academic toy” (XOR/CBC/DH) — belum kelihatan AEAD, TLS, password-KDF, side-channel, real misuse hunting. Telecom SMK = peluang soal RF/network, tapi CV project-nya lebih software. |

**Strategi crypto buat dia**: jangan nanya AES dari nol. **Tarik dari project-nya** (XOR/CBC/IV/DH), lalu dorong ke *kenapa itu belum cukup buat production/offensive-defensive lab*. Itu yang ngetes apakah dia hafal assignment atau beneran paham.

---

## Cara menilai cepat

| Signal | Artinya |
|--------|---------|
| Jawab konsep + trade-off | Bagus untuk riset |
| Langsung tools/nama tool tanpa alasan | Hafalan, belum mature |
| Bilang "ga tau" + kasih pendekatan | **Lebih bagus** dari ngarang |
| Ngarang technical detail | Red flag |
| Tanya clarifying question dulu | Green flag besar |

**Skoring kasar per soal (1–5)**  
1 = blank / ngasal · 2 = hafalan dangkal · 3 = paham dasar · 4 = paham + trade-off · 5 = berpikir seperti engineer (asumsi, limit, next step)

---

# BAGIAN A — Riset (hal pertama waktu belum ada referensi)

Ini yang paling penting buat lab kamu. Magang yang bagus bukan yang hafal CVE — yang tau **cara mulai dari nol**.

---

### A1. "Kamu ditugaskan riset fitur X di sistem Y. Belum ada paper, belum ada blog, belum ada PoC publik. Langkah pertama kamu apa — dari menit ke-0 sampai 1–2 hari pertama?"

**Maksud pertanyaan**  
Ngetes apakah dia punya *research muscle memory*, bukan cuma "buka Google / ChatGPT".

**Expected answer (arah yang bagus)**  
Urutan kira-kira gini (boleh beda urutan, yang penting logikanya):

1. **Clarify objective** — mau buktikan apa? (detect? exploit? harden? reverse?)
2. **Define success criteria** — "berhasil" itu bentuknya apa (evidence, marker, metric)
3. **Map surface** — input/output, trust boundary, privilege, protocol, file format
4. **Collect ground truth** — dokumen resmi, RFC, datasheet, source (kalau ada), binary sample, packet capture baseline
5. **Build minimal lab / harness** — lingkungan yang bisa diulang (Docker/VM), bukan langsung main di target "misterius"
6. **Instrument** — logging, pcap, debugger, frida, strace — biar tiap eksperimen ada jejak
7. **Hypothesis → experiment → note** — tulis asumsi, uji, revisi
8. **Negative control** — coba kasus yang *harusnya gagal*, biar ga kena false positive

Bonus bagus: bilang mau pisahin **behavior yang expected** vs **anomaly**, dan mau dokumentasikan gagal juga (failure notes berharga).

**Penjelasan buat kamu**  
Di industri militer/cyber research, sering banget kerja di area yang **tidak ada writeup**. Orang yang langsung loncat ke "exploit" tanpa harness biasanya nyasar. Yang kamu cari: disiplin eksperimen + reproducibility.

**What if jawabannya beda**

| Jawaban dia | Interpretasi | Follow-up |
|-------------|--------------|-----------|
| "Langsung Google / tanya AI" | Mungkin ok sebagai *satu* langkah, tapi dangkal | "Oke, 30 menit search gagal total. Langkah berikutnya?" |
| "Langsung decompile / reverse" | Agresif, bisa bagus kalau ada konteks binary | "Tanpa sample binary, kamu mulai dari mana?" |
| "Bikin tools dulu" | Sering premature | "Tools untuk ngerjain apa yang belum kamu ketahui?" |
| "Tanya senior" | Bukan salah, tapi incomplete | "Senior bilang: riset sendiri dulu, update 48 jam. Plan kamu?" |
| "Ga tau" + diam | Weak | Kasih hint: "Kalau kamu harus bikin lab kecil dulu, isinya apa?" |

**Follow-up default**  
- "Apa yang kamu tulis di day-1 notes biar orang lain bisa lanjut?"  
- "Bagaimana kamu bedain 'belum ketemu' vs 'memang ga ada'?"

---

### A2. "Kamu lagi riset protocol / format yang dokumentasinya jelek atau partial. Setelah 2 hari, hasilnya masih abu-abu. Gimana cara kamu putusin: lanjut gali, pivot, atau stop?"

**Maksud**  
Ngetes judgment & anti-sunk-cost. Magang sering nempel ke jalan buntu terlalu lama.

**Expected answer**  
Ada kriteria stop/pivot, misalnya:

- Evidence threshold: "kalau setelah N eksperimen terkontrol masih 0 signal usable → pivot"
- Cost vs value: effort naik, insight datar → stop sementara, tulis open questions
- Alternative path: ganti angle (blackbox → graybox, network → host, static → dynamic)
- Ask for constraint update: butuh hardware? akses source? sample lain?

Yang bagus: bilang **document dead ends** supaya ga diulang orang lain.

**What if**  
- Kalau dia bilang "gas terus sampe ketemu" → follow-up: "Budget waktu 1 minggu. Di hari ke-4 kamu masih stuck. Keputusan?"  
- Kalau dia langsung "stop" tanpa kriteria → "Stop berdasarkan apa? Feelings atau data?"

---

### A3. "Kamu nemu behavior aneh di lab (misal response beda 1 byte / timing beda 20ms). Ini bug, artifact lab, atau noise? Cara verifikasi?"

**Maksud**  
Scientific thinking. Cyber research sering kena false lead.

**Expected answer**  
- Reproduce di kondisi beda (restart, machine lain, timing lain)  
- Isolate variable (satu perubahan per eksperimen)  
- Bandingin dengan baseline "normal" yang sudah di-capture  
- Cek clock, buffering, TCP coalescing, antivirus, debugger presence  
- Baru naikkan ke hypothesis "vulnerability candidate"

**Follow-up**  
"Kalau cuma reproducible di mesinmu sendiri, kamu laporkan sebagai finding atau belum?"

---

# BAGIAN B — Cryptografi (disesuaikan CV RRWD)

Dia klaim project C: **XOR + CBC/IV + Diffie-Hellman + key management + cryptanalysis**.  
Jangan mulai dari “jelasin AES”. Mulai dari project-nya, lalu dorong ke limit & misuse — itu yang membedakan assignment lulus vs engineer yang siap lab.

**Urutan disarankan di sesi**: B0 → B1 → B2 → (pilih 1 dari B3/B4/B5). Jangan habisin semua.

---

### B0. Icebreaker project (wajib, 3–4 menit)

"Di CV kamu ada Cryptography & Cryptanalysis Tool di C — XOR, CBC + IV, Diffie-Hellman. Ceritain singkat: tool itu **ngapain aja**, input/output-nya apa, dan bagian mana yang paling susah waktu kamu implement?"

**Maksud**  
Verifikasi project real vs dibesar-besarin. Sekalian ambil vocabulary dia buat follow-up berikutnya.

**Expected answer (arah bagus)**  
Bisa jelasin alur CLI (encrypt/decrypt file atau string), di mana key disimpan/diinput, IV digenerate atau diinput user, DH cuma simulator 2 party di lokal, dan jujur soal limit (misal: belum authenticated encryption, belum network protocol beneran).

**Red flag**  
- Kabur: “ya encrypt decrypt gitu aja” tanpa detail IV/key  
- Ngarang fitur yang di CV ga ada (AES-GCM, RSA full PKI, dll)  
- Bilang “cryptanalysis” tapi yang dimaksud cuma brute XOR 1-byte

**What if**  
| Jawaban | Follow-up |
|---------|-----------|
| Detail rapi + sebut limit | Langsung loncat B1/B2 — kandidat promising |
| Hafalan slide | “Oke, skip teori. Di kodemu, IV-nya random tiap pesan atau fixed?” |
| “Cryptanalysis = decrypt pakai key” | “Bedanya cryptanalysis sama decrypt biasa apa?” |

---

### B1. XOR — “kenapa XOR sering muncul di kelas, tapi berbahaya kalau dipakai sendirian?”

**Konteks CV**: dia implement XOR cipher.

**Maksud**  
Ngetes dia paham XOR sebagai *building block* vs *cipher yang “aman”*. Di malware/offensive juga sering ketemu XOR obfuscation — relevan buat lab kamu.

**Expected answer**  
- XOR dengan key pendek / key reuse → trivial recover (known-plaintext, crib dragging, frequency)  
- `C1 ⊕ C2 = P1 ⊕ P2` kalau key sama dipakai dua plaintext  
- Bagus buat teaching / obfuscation ringan, **bukan** confidentiality modern  
- Bonus: sebut many-time pad

**Penjelasan buat kamu**  
Kalau dia defend “XOR aman kalau key panjangnya = pesan dan sekali pakai”, itu sebenernya one-time pad — bagus, tapi follow-up: “Di tool-mu, key-nya one-time pad beneran atau key pendek diulang?”

**What if**  
| Jawaban | Interpretasi | Follow-up |
|---------|--------------|-----------|
| “XOR aman” | Dangkal / salah | “Dua ciphertext XOR key yang sama. Attacker bisa apa?” |
| “XOR cuma buat belajar” | OK | “Kenapa malware masih suka XOR string?” (obfuscation, bukan crypto kuat) |
| Langsung OTP theory | Kuat | “Praktisnya kenapa OTP susah di-deploy?” (key distribution, key length, reuse risk) |

**Follow-up ofensif/defensif**  
- Offensive: “Kalau kamu nestress binary dan nemu XOR loop, langkah pertama analisis apa?”  
- Defensive: “Deteksi berbasis crypto strength vs deteksi berbasis behavior — XOR obfuscation masuk yang mana?”

---

### B2. CBC + IV — study case inti (paling pas sama CV-nya)

"Kamu implement CBC dengan IV. Dua skenario — pilih salah satu yang lebih parah, dan kenapa:

**(a)** IV selalu `0x00..00`  
**(b)** IV random, tapi dikirim di cleartext bareng ciphertext  

Lalu: CBC tanpa HMAC / auth tag — attacker yang bisa **modify ciphertext** di transit, impact-nya kira-kira apa?"

**Maksud**  
Ini langsung nancep ke klaim CV. Banyak mahasiswa “pakai IV” tapi ga paham IV role + malleability CBC.

**Expected answer**  
- **(a) lebih parah** untuk confidentiality pola: IV fixed → identical first-block plaintext menghasilkan identical first ciphertext block (mirip kelemahan “ECB-ish” di block pertama / leak equality). IV harus unik & unpredictable untuk CBC (random).  
- **(b) sebenernya normal**: IV **memang** biasanya dikirim/disimpan non-secret bareng ciphertext. Yang penting: unik + cukup random, jangan secret-kan IV sebagai ganti key.  
- **CBC tanpa auth**: ciphertext malleable — bit-flip di block C_i mempengaruhi P_{i+1} secara terkontrol; bisa rusak padding / corrupt field. Makanya butuh HMAC (encrypt-then-MAC) atau pindah ke **AES-GCM / ChaCha20-Poly1305**.

**Penjelasan buat kamu**  
Kalau dia bilang “(b) parah karena IV kebaca” → misconception klasik. Koreksi lembut, terus liat apakah dia nyambung. Itu signal belajar.

**What if**  
| Jawaban | Follow-up |
|---------|-----------|
| “(b) parah karena IV keliatan” | “Kalau IV harus rahasia, terus penerima decrypt pakai apa? Renungkan lagi (a) vs (b).” |
| “(a) parah, (b) OK” + sebut malleability | Strong — lanjut B3 atau B5 |
| Hanya hafal “IV biar beda ciphertext” | “IV reuse di CBC vs IV reuse di CTR/GCM — yang mana lebih ‘meledak’, dan kenapa?” |
| Ga pernah kepikiran auth | “Tool kamu bisa detect ciphertext diutak-atik, atau cuma decrypt apapun?” |

**Follow-up tajam (pilih satu)**  
1. “Padding oracle — pernah dengar? Dalam satu kalimat, ide attack-nya apa?” (bonus, ga wajib perfect)  
2. “Kalau kamu rewrite tool itu sekarang untuk lab militer, kamu ganti CBC ke mode apa — dan kenapa?”  
   Expected arah: GCM/AEAD atau libsiap pakai, jangan homemade.

---

### B3. Diffie-Hellman — dari simulator ke ancaman nyata

"DH di projectmu simulator secure key exchange. Pertanyaan: **DH sendiri tidak mengautentikasi siapa lawan bicara**. Di lab, MITM di tengah Alice–Bob itu ceritanya gimana, dan missing piece-nya apa?"

**Maksud**  
CV bilang “secure Diffie-Hellman”. Ngetes apakah dia paham DH = agreement, bukan authentication. Super relevan ke offensive MITM + defensive TLS.

**Expected answer**  
- Tanpa auth, attacker bisa DH terpisah ke Alice dan ke Bob → dua session key, relay/modify  
- Missing piece: autentikasi (signature, pre-shared identity, certificate / PKI, authenticated KEX seperti di TLS)  
- Bonus: sebut fingerprint/TOFU, atau “DH di dalam TLS dengan cert”

**What if**  
| Jawaban | Follow-up |
|---------|-----------|
| “DH sudah aman dari MITM” | “Attacker di tengah, Alice pikir dia ke Bob. Di mana asumsi DH pecah?” |
| Jelasin MITM + butuh cert/signature | Strong |
| Kabur ke math p,g,mod | “Skip angka. Security property yang *tidak* dijamin DH murni apa?” |

**Follow-up defensive**  
"Kalau app bilang ‘kami pakai DH’, checklist review kamu apa sebelum percaya klaim itu?"

---

### B4. “Cryptanalysis” di CV — uji kejujuran teknis

"CV-mu nulis cryptanalysis. Kasih contoh **satu** serangan atau analisis yang tool-mu benar-benar lakukan (atau yang kamu pahami end-to-end). Bukan nama keren — langkahnya."

**Maksud**  
Kata “cryptanalysis” di CV mahasiswa sering inflated. Kamu mau liat: frequency analysis XOR? brute key pendek? pad cracking? atau cuma marketing.

**Expected answer (yang masih acceptable level magang)**  
Contoh valid:  
- Frequency analysis / brute force XOR single-byte  
- Detect ECB vs CBC dari pola ciphertext  
- Demonstrate IV reuse leak  
- Known-plaintext recover XOR keystream  

Yang bagus: jujur “belum sampe differential/linear cryptoanalysis paper-level”.

**What if**  
| Jawaban | Interpretasi | Follow-up |
|---------|--------------|-----------|
| Jujur: “sebenarnya encrypt/decrypt + demo lemahnya XOR” | **Hijau** — maturity | “Kalau dikasih 1 minggu nambahin modul cryptanalysis yang berguna buat blue team, kamu pilih yang mana?” |
| Lempar istilah (linear cryptanalysis) tanpa langkah | Merah / hafalan | “Ok, buang istilahnya. Pakai plaintext `AAAA...` dan XOR key 1 byte — attacker recover key-nya gimana?” |
| Klaim break AES | Red flag besar | Minta detail; biasanya bubar |

---

### B5. Key management — klaim CV yang sering kosong

"Kamu tulis secure key management. Secara konkret di tool-mu: key lahir dari mana, disimpan di mana, pernah ada di log/argv/memory dump nggak, dan gimana key dikasih ke pihak kedua (selain DH simulator)?"

**Maksud**  
Di industri, key management > algoritma. Magang yang cuma `scanf` key lalu encrypt biasanya belum “key management”.

**Expected answer (arah)**  
Idealnya sadar masalah:  
- Key di command-line ketahuan `ps`  
- Key di file permission  
- Hardcoded key = mati  
- Perlu secret storage / env / user prompt tanpa echo  
- Separate encrypt key vs MAC key (kalau masih CBC+HMAC)  
- Rotation, kompromi key → blast radius  

Ga harus pernah implement HSM — yang penting dia **tahu gap-nya**.

**What if**  
- “Key diketik user” doang → “Itu input, belum management. Kalau proses di-crash dump, key masih di RAM. Di lab, kamu mitigate apa yang realistis?”  
- Langsung sebut KDF/password → sambungkan: “Password ke key: SHA-256 sekali vs PBKDF2/Argon2 — bedanya apa?”

---

### B6. Jembatan ke kerja lab kamu (opsional, kalau sisa waktu)

"Anggap tool C-mu mau dipakai di riset offensive/defensive militer — misalnya analisis protocol atau buat detection terhadap crypto jelek. **Satu fitur** yang paling worth kamu tambah dulu apa, dan kenapa bukan fitur lain?"

**Expected arah (salah satu cukup)**  
- Ganti ke AEAD (GCM) + test vectors  
- Deteksi otomatis weak pattern (ECB-like repeat, IV zero, XOR reuse) buat **defensive scanner**  
- Interop dengan pcap (cari high-entropy payload / bad TLS)  
- Jangan jawab “bikin algoritma sendiri”

**Follow-up**  
"Ini riset tanpa banyak referensi implementasi internal. Hari pertama kamu ngapain?" → link balik ke A1.

---

### B7. Cadangan klasik (kalau project talk terlalu cepat / dia kuat)

Tetap berguna sebagai pembanding depth:

**B7a.** "Hash password pakai SHA-256 — cukup? Kenapa?"  
Expected: tidak; butuh slow KDF (Argon2/bcrypt) + salt.

**B7b.** "TLS sudah encrypt, MITM masih mungkin — skenario lab realistis?"  
Expected: trust rogue CA, disable verify, pinning lemah, mixed HTTP API — bukan “TLS broken”.

**B7c.** Pseudocode jelek:

```
key = SHA256(password)
cbc_encrypt(key, plaintext, iv=0)
kirim ciphertext
```

"Apa yang salah? Fix praktisnya?"  
Expected: IV fixed, KDF naif, no auth → pakai Argon2/PBKDF2, random IV/nonce, AES-GCM, atau jangan custom (pakai libsodium/TLS).

---

# BAGIAN C — Development (coding / engineering)

Ini ngetes apakah dia bisa *bikin tool*, bukan cuma pakai tool.

---

### C1. "Kamu disuruh bikin port scanner kecil (educational/lab). Kamu pilih connect-scan atau SYN-scan. Trade-off-nya apa, dan untuk magang lab kamu pilih yang mana dulu?"

**Maksud**  
System programming sense + prioritas delivery.

**Expected answer**  
- Connect (TCP handshake penuh): simple, ga perlu raw socket/root, reliable, lebih "noisy"/mudah di-log  
- SYN: lebih rendah di stack, butuh privilege, lebih kompleks, partial stealth (bukan invisible)

Untuk magang/awal: **connect dulu** biar benar, baru SYN kalau perlu. Yang bagus juga sebut rate limit, timeout, concurrency, output JSON.

**What if**  
- Langsung "SYN karena lebih pro" tanpa alasan → "Di Windows/mac tanpa admin, kamu stuck. Plan B?"  
- Ga tau bedanya → ajarin singkat, lalu tanya ulang trade-off

**Follow-up**  
"Kalau target 10.000 port, kenapa naive thread-per-port bisa jelek? Alternatif?"

---

### C2. "Tool offensive kamu crash di tengah jalan setelah ubah firewall target. Apa yang kurang dari desain tool-nya?"

**Maksud**  
Engineering hygiene: cleanup, idempotency, failure handling — krusial di lab militer.

**Expected answer**  
Kurang: cleanup/finally, state tracking (apa yang diubah), timeout, dry-run/check mode, logging aksi, rollback, signal handler (Ctrl+C), scope allowlist.

**Follow-up**  
"Kalau kamu design CLI, flag wajib apa biar orang lain ga nembak salah target?"

Expected arah: `--target`, `--scope`/`--confirm-lab-scope`, `--mode check|exploit`, `--dry-run`, output evidence path.

---

### C3. "Bedanya bug, vulnerability, dan exploit — dalam konteks development tool."

**Maksud**  
Bahasa profesional. Banyak magang campur ketiga ini.

**Expected answer**  
- **Bug**: perilaku salah / defect  
- **Vulnerability**: bug (atau misconfig) yang *bisa disalahgunakan* untuk security impact  
- **Exploit**: kode/prosedur yang *memanfaatkan* vulnerability secara reliable  

Bonus: PoC ≠ weaponized exploit.

**Follow-up**  
"Kamu nemu crash di parser. Langkah buat nentuin ini cuma bug atau sudah jadi vuln?"

---

### C4. Mini coding discussion (boleh whiteboarding, ga harus nulis sempurna):

"Fungsi `is_admin(user_id)` di API dipanggil dari client. Client kirim `{"user_id": 7, "is_admin": true}`. Apa yang salah secara desain?"

**Expected**  
Trust boundary salah. Client-controlled field ga boleh jadi sumber otorisasi. AuthZ harus server-side dari session/token + DB role.

**What if**  
- Fokus ke "validasi tipe data" doang → dorong: "Walaupun tipenya bener, kenapa tetap bahaya?"

**Follow-up**  
"Kalau IDOR, pola fix-nya apa yang kamu expect di code review?"

---

### C5. "Kamu build detection rule (Suricata/Sigma). Rule-mu kepicu di traffic lab yang kamu tandai, tapi di production palsu terus. Diagnosis?"

**Maksud**  
Defensive development maturity: false positive thinking.

**Expected**  
Rule terlalu brittle / terlalu generic; lab marker kebawa ke rule; kurang negative control; field mapping beda; baseline traffic beda; butuh contextual filter (subnet, user, process parent).

**Follow-up**  
"Lebih aman: rule ketat rendah FP, atau rule longgar tinggi coverage? Tergantung apa?"

---

# BAGIAN D — Offensive development (study case)

Level magang: konsep + pendekatan, bukan minta full malware chain.

---

### D1. Web — SSRF  
"Endpoint `/fetch?url=` fetch URL dari server. Allowlist hanya host yang mengandung `company.internal`. Bypass ide apa yang masuk akal, dan evidence apa yang kamu cari di lab?"

**Maksud**  
Parsing/allowlist naif. Classic tapi masih sering lolos.

**Expected answer (arah)**  
Ide bypass (sebut 2–3 cukup):

- `company.internal.evil.com` (suffix/prefix confusion)  
- redirect ke internal setelah allowlist check  
- IP literal / decimal / IPv6 / DNS rebinding  
- `localhost` encoded, `@` confusion di URL, dll (yang penting: dia paham *parser mismatch*)

Evidence lab: response mengandung marker internal service / dummy metadata token — **bukan** nyentuh cloud beneran.

**What if**  
- Langsung kasih 10 payload random tanpa alasan → "Pilih 1, jelasin kenapa allowlist itu gagal."  
- Bilang "SSRF ga mungkin kalau ada allowlist" → kasih counterexample di atas

**Follow-up**  
"Fix defensive yang bener: allowlist string, atau allowlist resolved IP + block private ranges + no redirect? Kenapa?"

---

### D2. Network — MITM lab  
"Di lab Docker: victim, target HTTP, attacker. Kamu mau tunjukin integrity impact (response diubah). Urutan kerja yang aman & profesional?"

**Expected**  
1. Scope pair victim↔target  
2. Baseline request (before)  
3. Enable forwarding / ARP spoof **hanya pasangan itu**  
4. Intercept + modify (marker header/body)  
5. Verify victim terima marker  
6. Evidence: pcap + before/after  
7. Cleanup: restore ARP, iptables, stop forwarding  

Yang bagus sebut: default check mode, confirm flag, jangan broadcast scam.

**Follow-up**  
"Kenapa cleanup dianggap bagian dari exploit engineering, bukan 'nice to have'?"

---

### D3. "Kamu diminta bikin PoC RCE. Default mode tool-nya exploit atau check? Kenapa?"

**Expected**  
Default **check/non-destructive**. Exploit opt-in. Alasan: safety, audit, kurangin accident di lab share.

**What if** "Default exploit biar keren" → red flag OPSEC/engineering.

---

### D4. Malware-dev level magang (konsep, bukan minta warhead)  
"Implant lab harus 'keluar' ke C2. Dari sisi defensive, sinyal apa yang relatif stabil buat dideteksi — dibanding hash file?"

**Maksud**  
Dorong behavior detection, bukan antivirus signature mindset.

**Expected**  
Network beacon pattern, unusual child process, persistence location, signed-binary proxy execution, DNS anomalous, dll. Hash gampang diganti.

**Follow-up**  
"Kalau offensive researcher sadar deteksi itu, apa yang biasanya mereka ubah dulu — dan dari sisi blue, kamu antisipasi apa?"

(Jaga tetap lab/authorized framing; fokus cat-and-mouse engineering.)

---

### D5. Linux / privilege  
"Binary SUID owned by root, kelihatan simple. Langkah riset pertama sebelum 'cari exploit di Google'?"

**Expected**  
- `file`, check permissions, `readelf`/`ldd`  
- strings / options yang dangerous (command inject, writable config, relative path)  
- jalankan dengan input aneh di lab  
- cek apakah call external command tanpa path absolut  
- baru bandingkan dengan known classes (bukan CVE hunting buta)

**Follow-up**  
"Kenapa relative path di SUID program sering jadi masalah?"

---

# BAGIAN E — Defensive development

---

### E1. "Tim red nemuin XSS stored. Sebagai defensive engineer, deliverable kamu apa selain 'tolong sanitize'?"

**Expected**  
- Root cause di code path (sink + missing encode context)  
- Patch konkret (context-aware encoding, CSP, cookie flags)  
- Regression test  
- Detection/log signal (kalau relevan)  
- Verify fix dengan PoC yang sama (harus gagal)  
- Cek XSS sejenis di endpoint lain (pattern hunt)

**Follow-up**  
"Kenapa 'pakai blacklist `<script>`' biasanya gagal sebagai fix utama?"

---

### E2. "Kamu punya pcap serangan lab. Mau bikin Suricata rule. Langkah biar rule-nya ga cuma hafalin 1 string unik dari PoC?"

**Expected**  
Cari invariant behavior (protocol anomaly, header pattern yang memang bagian teknik, sequence), test positive + **negative control**, tulis false positive notes, jangan overfit ke lab marker kecuali marker memang untuk training detection.

**What if** dia copy exact payload → "Attacker ubah 1 karakter. Rule mati. Gimana?"

---

### E3. "Logging: app log 'login failed' aja. Untuk investigasi brute force / credential stuffing, field apa yang kurang?"

**Expected**  
timestamp, src IP, username (hati-hati PII policy), user-agent, result reason, request_id, geo/ASN (opsional), rate, success/fail, correlation id. Jangan log password.

**Follow-up**  
"Kalau terlalu banyak log, detection justru jelek. Gimana komprominya?"

---

# BAGIAN F — RF / WiFi / frekuensi (karena scope industri kamu)

Tetap level magang: safety + konsep, bukan minta jamming liar.

---

### F1. "Kenapa riset TX (transmit) di RF beda banget dari riset software exploit, dari sisi tanggung jawab lab?"

**Expected**  
RF bisa spill ke luar lab → interferensi layanan nyata, isu legal/lisensi. Butuh Faraday / shielding, power limit, test PLMN, timer auto-off, konfirmasi environment. Software exploit salah target masih di jaringan; RF salah setup bisa ngenai orang luar.

**Follow-up**  
"Kalau belum ada Faraday cage, aktivitas apa yang masih boleh vs yang wajib ditunda?"

Expected arah: RX/capture/analisis sering masih oke; TX/jam/BTS sering harus ditunda.

---

### F2. "WiFi deauth itu ngapain di level protokol, dan kenapa 'berhasil deauth' belum tentu berarti kamu punya credential?"

**Expected**  
Deauth = management frame yang nyuruh client putus. Itu DoS / paksa reconnect; credential/handshake capture itu langkah terpisah. Banyak orang campur "ganggu WiFi" dengan "masuk WiFi".

**Follow-up**  
"Dalam engagement authorized, kapan deauth masuk akal, dan kapan justru kontraproduktif?"

---

# BAGIAN G — Android / lintas platform (ringkas)

---

### G1. "Android app bypass SSL pinning. Dari sudut offensive lab vs defensive hardening — masing-masing objective-nya apa?"

**Expected**  
Offensive lab: biar bisa intercept API secara authorized untuk analysis.  
Defensive: pinning + root detect bukan silver bullet; fokus certificate validation bener, attestation, minimize secret di client, server-side authZ.

Yang bagus: bilang pinning di client **bisa dibypass** kalau attacker kontrol device — jadi jangan taruh trust berlebih di client.

---

### G2. "Secret API key di APK. Kenapa 'diobfuscate' sering enggak cukup?"

**Expected**  
APK di tangan user = reverseable. Obfuscation naikkan cost, bukan hilangkan secret. Secret yang sensitive harus di server.

---

# BAGIAN H — Soft-technical judgment (tetap study case)

---

### H1. "Temenmu kirim 'full exploit' tanpa README, tanpa lab harness, tanpa cleanup. Kamu mau merge ke repo riset tim? Kenapa?"

**Expected**  
Tolak / minta perbaikan dulu. Alasan: reproducibility, safety, audit, onboarding orang lain, risiko salah pakai.

Ini soal culture engineering di lab militer — sangat relevan.

---

### H2. "Kamu punya 3 hari. Pilih: (a) tool setengah jadi tapi measurable, (b) slide teori lengkap tanpa artefak. Pilih mana buat demo ke lead?"

**Expected**  
Umumnya (a) — di research org, evidence > narasi. Tapi harus jujur soal limit.

---

# PAKET REKOMENDASI SESI (60 menit) — khusus RRWD

**Warm-up (8 menit)**  
A1 (riset tanpa referensi) — tetap, karena background-nya academic project, belum kelihatan research-from-scratch.

**Crypto block (15–18 menit) — wajib karena ini “highlight” CV-nya**  
B0 → B1 → B2 → B3  
Kalau B0–B2 sudah kuat: sisipkan B4 (uji kata “cryptanalysis”) atau B5 (key management).  
Kalau goyah di CBC/IV: jangan paksain B3; ganti B7c biar tetap ada signal.

**Core mix sisa (20–25 menit)** — dia C + Linux + telecom SMK:

| Prioritas | Soal | Alasan |
|-----------|------|--------|
| Tinggi | C1 atau C2 | C/low-level + engineering hygiene |
| Tinggi | D1 atau D2 | offensive lab thinking |
| Medium | F1 | SMK Telkom / akses jaringan — liat transfer ke RF safety |
| Medium | E1 atau C4 | defensive / trust boundary |
| Skip dulu | G1/G2 Android | ga muncul di CV |

**Closing (8–10 menit)**  
B6 (jembatan ke lab kamu) **atau** H1 (merge exploit tanpa harness) — ownership.

### Cheat sheet crypto khusus dia

| Signal | Artinya |
|--------|---------|
| Jujur limit project (XOR toy, DH tanpa auth) | Mature — lean hire crypto-wise |
| Bilang IV harus rahasia | Misconception klasik — koreksi; kalau langsung nyambung = trainable |
| Defend XOR sebagai “secure encryption” | Dalam pemahaman lemah |
| “Cryptanalysis” = cuma decrypt | Inflated CV; ga fatal kalau jujur |
| Usul AEAD / jangan homemade protocol | Siap masuk lab offensive-defensive |
| Ngarang break AES / linear cryptanalysis tanpa langkah | Lean no di area crypto |

---

# PAKET REKOMENDASI SESI (60 menit) — generik (kandidat lain)

**Warm-up (8 menit)**  
A1 (riset tanpa referensi)

**Core mix (40 menit)** — pilih sesuai background kandidat:

| Track | Soal |
|-------|------|
| Umum / full-stack cyber | B7a/B7c, C2, D1, E1 |
| Lebih coding | C1, C4, B7c, D3 |
| Lebih defensive | E2, E3, B7b, C5 |
| Ada minat RF/WiFi | F1, F2, A3 |
| Ada minat mobile | G1, G2, B7b |
| Mirip RRWD (XOR/CBC/DH project) | B0–B3, C2, D1 |

**Closing (10 menit)**  
A2 atau H1 — liat maturity & ownership

---

# CHEAT SHEET — sinyal hire / no-hire (magang)

**Lean hire**  
- Clarifying question natural  
- Bilang asumsi dengan eksplisit  
- Pikirin cleanup, scope, evidence  
- "Ga tau, tapi pendekatan saya..."  
- Bedain hash vs password-KDF, encrypt vs authenticated encrypt  
- (RRWD) paham IV CBC boleh publik, IV reuse/fixed berbahaya; DH ≠ auth; XOR ≠ modern cipher  

**Lean no**  
- Hafalan tools tanpa mekanisme  
- Ngarang CVE/detail  
- Default dangerous mode  
- Abai legal/lab safety di RF  
- "Saya langsung serang production biar real"  
- (RRWD) ngarang cryptanalysis berat / bilang AES broken tanpa syarat  

**Lean maybe (bisa dilatih)**  
- Dasar lemah tapi struktur pikir rapi  
- Kurang vocabulary tapi eksperimen mindset ada  
- Salah jawaban crypto tapi mau dikoreksi dan langsung nyambung  
- (RRWD) project academic dangkal tapi jujur + cepat catch-up ke AEAD/MITM 

---

# CATATAN OPSEC BUAT INTERVIEWER

- Jangan minta kandidat bikin malware operasional / target nyata di sesi interview.  
- Framing selalu: lab, authorized, harness, detection, cleanup.  
- Kalau jawaban ke arah criminal misuse, redirect ke lab scope — itu juga data soal judgment.

---

*Internal — Security Research Lab interview pack. Sesuaikan bobot soal dengan role magang (red/blue/RF/dev).*
