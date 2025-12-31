import customtkinter as ctk

# ==============================================================================
# PROJE: NEXUS CONTROL HUB - ANA BAŞLATICI (ENTRY POINT)
# YAZAR: [Senin Adın]
# TARİH: 2025
# AÇIKLAMA: Bu dosya uygulamanın çalıştırılacağı ana dosyadır (main.py).
#           Arayüz kodlarını (GUI) modüler tutmak için ayrı bir dosyadan çağırır.
# ==============================================================================

# "modern_home_automation_gui.py" dosyasının içindeki ana sınıfı (Class) dahil ediyoruz.
# Böylece binlerce satır kodu tek dosyada tutmak yerine parçalara bölmüş oluyoruz.
from modern_home_automation_gui import ModernHomeAutomationGUI

if __name__ == "__main__":
    # 1. Ana Pencere Nesnesini (Root) Oluştur
    # CustomTkinter'ın temel pencere yapısını başlatır.
    app = ctk.CTk()

    # 2. Uygulama Arayüzünü Yükle
    # Oluşturduğumuz pencereyi (app), diğer dosyadaki sınıfa parametre olarak gönderiyoruz.
    # Bu işlem, tüm butonları, etiketleri ve tasarımı pencereye yerleştirir.
    gui = ModernHomeAutomationGUI(app)

    # 3. Sonsuz Döngüyü Başlat (Main Loop)
    # Bu komut, kullanıcı pencereyi kapatana kadar programın açık kalmasını sağlar.
    app.mainloop()