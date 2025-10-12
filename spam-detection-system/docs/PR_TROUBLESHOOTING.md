# Pemecahan Masalah Push PR

Jika Anda mengalami kegagalan saat menjalankan `git push` untuk mengirim perubahan ke pull request, periksa konfigurasi remote repository terlebih dahulu.

## Tidak Ada Remote yang Terpasang

### Gejala
```
fatal: No configured push destination.
Either specify the URL from the command-line or configure a remote repository using

    git remote add <name> <url>

and then push using the remote name

    git push <name>
```

### Penyebab
Perintah `git remote -v` tidak menampilkan entri apa pun sehingga Git tidak mengetahui ke mana harus mengirim commit terbaru.

### Solusi
1. Tambahkan remote repository yang sesuai:
   ```bash
   git remote add origin https://github.com/organisasi/proyek.git
   ```
2. Pastikan kredensial akses valid (SSH key atau token).
3. Jalankan perintah push dengan menyebutkan remote dan branch:
   ```bash
   git push origin work
   ```

Setelah remote terkonfigurasi, perintah `git push` akan berhasil dan PR dapat diperbarui.
