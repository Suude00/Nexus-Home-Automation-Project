import serial
import time

# ==============================================================================
# PROJE: NEXUS CONTROL HUB - API KATMANI (BACKEND)
# YAZAR: Suude Kaynak - 152120211110
# TARİH: 2025
# AÇIKLAMA: Bu dosya, bilgisayar ile PIC mikrodenetleyiciler arasındaki
#           seri haberleşme (UART) protokolünü yönetir.
#           Ödev PDF'indeki bit manipülasyonu ve komut setleri burada uygulanır.
# ==============================================================================

# --- KOMUT SETİ (PROTOKOL TANIMLARI) ---
# PIC yazılımında tanımlanan "Command" byte'ları ile buradakiler birebir aynı olmalıdır.
# Bu kodlar, PIC'e "Bana şu veriyi gönder" demek için kullanılır.

# BOARD #1: KLİMA KONTROL ÜNİTESİ (AC UNIT)
CMD_AC_GET_DESIRED_TEMP_FRAC = 0b00000001  # İstenen Sıcaklık (Ondalık Kısım)
CMD_AC_GET_DESIRED_TEMP_INT  = 0b00000010  # İstenen Sıcaklık (Tam Sayı Kısım)
CMD_AC_GET_AMBIENT_TEMP_FRAC = 0b00000011  # Ortam Sıcaklığı (Ondalık Kısım)
CMD_AC_GET_AMBIENT_TEMP_INT  = 0b00000100  # Ortam Sıcaklığı (Tam Sayı Kısım)
CMD_AC_GET_FAN_SPEED         = 0b00000101  # Fan Hızı (RPS)

# BOARD #2: PERDE VE SENSÖR ÜNİTESİ (CURTAIN & SENSORS)
CMD_CUR_GET_DESIRED_FRAC      = 0b00000001 # Perde Hedef (Ondalık - Opsiyonel)
CMD_CUR_GET_DESIRED_INT       = 0b00000010 # Perde Hedef (Tam Sayı)
CMD_CUR_GET_OUTDOOR_TEMP_FRAC = 0b00000011 # Dış Sıcaklık (Ondalık)
CMD_CUR_GET_OUTDOOR_TEMP_INT  = 0b00000100 # Dış Sıcaklık (Tam Sayı)
CMD_CUR_GET_PRESSURE_FRAC     = 0b00000101 # Basınç (Düşük Byte)
CMD_CUR_GET_PRESSURE_INT      = 0b00000110 # Basınç (Yüksek Byte)
CMD_CUR_GET_LIGHT_FRAC        = 0b00000111 # Işık (Düşük Byte)
CMD_CUR_GET_LIGHT_INT         = 0b00001000 # Işık (Yüksek Byte)

# --- VERİ GÖNDERME FORMATI (BIT MASKELEME) ---
# PC'den PIC'e veri gönderirken, verinin ne olduğunu (Header) ve
# verinin kendisini (Data) tek bir byte içine sıkıştırıyoruz.
# PDF Sayfa 16-19 referans alınmıştır.
MASK_SET_FRAC_HEADER = 0b10000000  # Header: 10xxxxxx (Ondalık ayarlama komutu)
MASK_SET_INT_HEADER  = 0b11000000  # Header: 11xxxxxx (Tam sayı ayarlama komutu)
MASK_DATA_6BIT       = 0x3F        # 00111111 (Son 6 biti almak için filtre)


class HomeAutomationSystemConnection:
    """
    Temel Haberleşme Sınıfı (Base Class).
    Seri portu açma, kapama, byte gönderme ve okuma gibi
    düşük seviyeli işlemleri yönetir.
    """
    def __init__(self, comPort="COM1", baudRate=9600):
        self.comPort = comPort
        self.baudRate = baudRate
        self.serial_port = None

    def open(self):
        """Seri port bağlantısını açar."""
        try:
            self.serial_port = serial.Serial(self.comPort, self.baudRate, timeout=1)
            print(f"Bağlantı Açıldı: {self.comPort}")
            return True
        except Exception as e:
            print(f"Hata ({self.comPort}): {e}")
            return False

    def close(self):
        """Seri port bağlantısını güvenli şekilde kapatır."""
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            return True
        return False

    def _send_byte(self, byte_data):
        """
        PIC'e tek bir byte gönderir.
        ÖNEMLİ: PIC işlemcileri PC kadar hızlı değildir. Veriyi işleyebilmesi için
        her gönderimden sonra çok kısa (0.02sn) bir bekleme eklenmiştir.
        """
        if self.serial_port and self.serial_port.is_open:
            try:
                self.serial_port.write(bytes([byte_data]))
                time.sleep(0.02)  # Buffer taşmasını önlemek için bekleme
            except:
                pass

    def _read_byte(self):
        """PIC'ten gelen tek bir byte veriyi okur."""
        if self.serial_port and self.serial_port.is_open:
            try:
                data = self.serial_port.read(1)
                if data:
                    return int.from_bytes(data, byteorder='big')
            except:
                pass
        return 0  # Veri gelmezse veya hata olursa 0 dön


class AirConditionerSystemConnection(HomeAutomationSystemConnection):
    """
    BOARD #1 (Klima Sistemi) için özel kontrol sınıfı.
    Ana sınıftan miras alır (Inheritance).
    """
    def __init__(self, com_port):
        super().__init__(comPort=com_port)
        self.desiredTemperature = 25.0
        self.ambientTemperature = 0.0
        self.fanSpeed = 0

    def update(self):
        """
        PIC'ten güncel verileri (Sıcaklık, Fan vb.) çeker.
        Sorgu-Cevap (Polling) mantığıyla çalışır.
        """
        # 1. Ortam Sıcaklığını İste (Önce Tam sayı, Sonra Ondalık)
        self._send_byte(CMD_AC_GET_AMBIENT_TEMP_INT)
        amb_int = self._read_byte()
        self._send_byte(CMD_AC_GET_AMBIENT_TEMP_FRAC)
        amb_frac = self._read_byte()
        # Birleştirme: Tam + (Ondalık / 10) -> Örn: 22 + 0.5 = 22.5
        self.ambientTemperature = amb_int + (amb_frac / 10.0)

        # 2. İstenen Sıcaklığı İste (Senkronizasyon amacıyla)
        self._send_byte(CMD_AC_GET_DESIRED_TEMP_INT)
        des_int = self._read_byte()
        self._send_byte(CMD_AC_GET_DESIRED_TEMP_FRAC)
        des_frac = self._read_byte()
        self.desiredTemperature = des_int + (des_frac / 10.0)

        # 3. Fan Hızını İste
        self._send_byte(CMD_AC_GET_FAN_SPEED)
        self.fanSpeed = self._read_byte()

    def setDesiredTemp(self, temp):
        """
        Kullanıcının girdiği hedef sıcaklığı PIC'e gönderir.
        Burada 'Bit Masking' ve 'Bitwise OR' işlemleri kullanılır.
        """
        # Sayıyı parçala: 25.5 -> Tam: 25, Ondalık: 5
        val_int = int(temp)
        val_frac = int((temp - val_int) * 10)

        # ADIM 1: Ondalık Kısmı Paketle (Header: 10xxxxxx)
        # Örnek: Header(10000000) OR Data(00000101) = 10000101
        cmd_frac = MASK_SET_FRAC_HEADER | (val_frac & MASK_DATA_6BIT)
        self._send_byte(cmd_frac)

        # ADIM 2: Tam Sayı Kısmı Paketle (Header: 11xxxxxx)
        cmd_int = MASK_SET_INT_HEADER | (val_int & MASK_DATA_6BIT)
        self._send_byte(cmd_int)

        self.desiredTemperature = temp

    # Getter Metotları (Arayüzün veriye ulaşması için)
    def getAmbientTemp(self): return self.ambientTemperature
    def getFanSpeed(self): return self.fanSpeed
    def getDesiredTemp(self): return self.desiredTemperature


class CurtainControlSystemConnection(HomeAutomationSystemConnection):
    """
    BOARD #2 (Perde ve Sensör Sistemi) için özel kontrol sınıfı.
    """
    def __init__(self, com_port):
        super().__init__(comPort=com_port)
        self.curtainStatus = 0.0
        self.outdoorTemp = 0.0
        self.outdoorPress = 0.0
        self.lightIntensity = 0.0

    def update(self):
        """PIC'ten sensör verilerini çeker."""
        # 1. Dış Sıcaklık Okuma
        self._send_byte(CMD_CUR_GET_OUTDOOR_TEMP_INT)
        t_int = self._read_byte()
        self._send_byte(CMD_CUR_GET_OUTDOOR_TEMP_FRAC)
        t_frac = self._read_byte()
        self.outdoorTemp = t_int + (t_frac / 10.0)

        # 2. Hava Basıncı Okuma (Basitleştirilmiş birleştirme)
        self._send_byte(CMD_CUR_GET_PRESSURE_INT)
        p_int = self._read_byte()
        self._send_byte(CMD_CUR_GET_PRESSURE_FRAC)
        p_frac = self._read_byte()
        self.outdoorPress = (p_int * 10) + p_frac

        # 3. Işık Şiddeti Okuma
        self._send_byte(CMD_CUR_GET_LIGHT_INT)
        l_int = self._read_byte()
        self.lightIntensity = l_int * 10  # Ham veriyi Lux cinsine benzetmek için çarpan

    def setCurtainStatus(self, status):
        """
        Perde açıklığını (%) ayarlar.
        Bit manipülasyonu klima ile benzer mantıktadır.
        """
        val_int = int(status)  # Perde %0-100 (Tam sayı yeterli)

        # Paketleme: Header(11xxxxxx) | Data(xxxxxx)
        cmd_int = MASK_SET_INT_HEADER | (val_int & MASK_DATA_6BIT)
        self._send_byte(cmd_int)

        self.curtainStatus = status

    # Getter Metotları
    def getOutdoorTemp(self): return self.outdoorTemp
    def getOutdoorPress(self): return self.outdoorPress
    def getLightIntensity(self): return self.lightIntensity