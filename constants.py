# ==============================================================================
# PROJE: NEXUS CONTROL HUB - YAPILANDIRMA DOSYASI (CONFIG)
# YAZAR: Suude Kaynak - 152120211110
# TARİH: 2025
# AÇIKLAMA: Bu dosya, projenin genel ayarlarını (Portlar, Sabitler vb.) içerir.
#           Kodun içinde tek tek port değiştirmek yerine, sadece burayı değiştiririz.
# ==============================================================================

# --- SERİ PORT AYARLARI (HABERLEŞME KÖPRÜSÜ) ---
# Bilgisayar (Python) ile PICSimLab (Simülasyon) arasında veri taşımak için
# "Sanal Seri Port Çiftleri" (Virtual Serial Port Pairs) kullanılır.
# ÖNEMLİ: Bir uca Python, diğer uca PIC bağlanmalıdır.

# ------------------------------------------------------------------------------
# BOARD #1: KLİMA SİSTEMİ (AC UNIT)
# ------------------------------------------------------------------------------
# Eltima Ayarı: COM1 <---> COM2 (Birbirine bağlı çift)
# Python Yazılımı -> COM1 Portunu dinler.
# PICSimLab       -> COM2 Portunu kullanmalıdır.
AC_BOARD_PORT = "COM1"

# ------------------------------------------------------------------------------
# BOARD #2: PERDE VE SENSÖR SİSTEMİ (CURTAIN & SENSORS)
# ------------------------------------------------------------------------------
# Eltima Ayarı: COM3 <---> COM4 (İkinci bir çift oluşturulmalı)
# Python Yazılımı -> COM4 Portunu dinler.
# PICSimLab       -> COM3 Portunu kullanmalıdır.
CURTAIN_BOARD_PORT = "COM4"

# --- NOT ---
# Eğer bağlantı hatası alırsanız:
# 1. Eltima (Virtual Serial Port Driver) programını kontrol edin.
# 2. Çiftlerin doğru oluşturulduğundan emin olun (Örn: COM1 ile COM2 eşleşmeli).
# 3. PICSimLab'de doğru portun (Python'un tersi) seçili olduğuna emin olun.