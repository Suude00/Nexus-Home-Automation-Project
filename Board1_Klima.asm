;====================================================================
; PROJE: Ev Otomasyonu - Board #1 (KLIMA SISTEMI)
; MODUL: UART Haberlesme + ADC Okuma + Fan Kontrol
; FREKANS: 20 MHz
;====================================================================

PROCESSOR 16F877A
#include <xc.inc>

; Konfigurasyon: HS Osilator, Watchdog Kapali, LVP Kapali
CONFIG FOSC = HS
CONFIG WDTE = OFF
CONFIG PWRTE = ON
CONFIG BOREN = OFF
CONFIG LVP = OFF
CONFIG CPD = OFF
CONFIG WRT = OFF
CONFIG CP = OFF

;====================================================================
; DEGISKENLER (RAM)
;====================================================================
PSECT udata_bank0
RX_TEMP:            DS 1    ; Gelen veri saklama
W_TEMP:             DS 1    ; Interrupt sirasinda W yedegi
STATUS_TEMP:        DS 1    ; Interrupt sirasinda STATUS yedegi

DESIRED_TEMP_INT:   DS 1    ; Istenen Sicaklik (Tam Sayi)
DESIRED_TEMP_DEC:   DS 1    ; Istenen Sicaklik (Ondalik)
AMBIENT_TEMP_INT:   DS 1    ; Ortam Sicakligi (Tam Sayi)
AMBIENT_TEMP_DEC:   DS 1    ; Ortam Sicakligi (Ondalik)
FAN_SPEED_RPS:      DS 1    ; Fan Hizi

;====================================================================
; PROGRAM BASLANGICI
;====================================================================
PSECT resetVec, class=CODE, delta=2
resetVec:
    PAGESEL SETUP
    GOTO SETUP

PSECT intVec, class=CODE, delta=2
ORG 0x004
intVec:
    PAGESEL ISR_HANDLER
    GOTO ISR_HANDLER

;====================================================================
; ANA PROGRAM
;====================================================================
PSECT code

SETUP:
    ; --- BANK 1 AYARLARI ---
    BANKSEL ADCON1
    
    ; Analog/Dijital Ayarlari
    MOVLW 0x8E          ; RA0 Analog, Digerleri Dijital
    MOVWF BANKMASK(ADCON1)
    
    ; Port Yonlendirmeleri (1=Giris, 0=Cikis)
    MOVLW 0x01          ; RA0 Giris
    MOVWF BANKMASK(TRISA)
    MOVLW 0xF0          ; Keypad
    MOVWF BANKMASK(TRISB)
    MOVLW 0x80          ; RC7(RX)=Giris, RC6(TX)=Cikis
    MOVWF BANKMASK(TRISC)
    MOVLW 0x00          ; PORTD Cikis (Motorlar icin)
    MOVWF BANKMASK(TRISD)
    
    ; UART Ayarlari (9600 Baud @ 20MHz)
    MOVLW 129           ; SPBRG degeri
    MOVWF BANKMASK(SPBRG)
    BSF BANKMASK(TXSTA), TXSTA_BRGH_POSN     ; Yuksek hiz modu
    BCF BANKMASK(TXSTA), TXSTA_SYNC_POSN     ; Asenkron mod
    BSF BANKMASK(TXSTA), TXSTA_TXEN_POSN     ; Gonderim (TX) acik
    BSF BANKMASK(PIE1), PIE1_RCIE_POSN       ; Alma (RX) kesmesi acik
    
    ; --- BANK 0 AYARLARI ---
    BANKSEL RCSTA
    
    BSF BANKMASK(RCSTA), RCSTA_SPEN_POSN     ; Seri portu aktif et
    BSF BANKMASK(RCSTA), RCSTA_CREN_POSN     ; Surekli veri alimini ac
    
    ; ADC Ayarlari
    MOVLW 0x81          ; Fosc/32, Kanal 0, ADC Acik
    MOVWF BANKMASK(ADCON0)
    
    ; Kesmeleri (Interrupts) Ac
    BSF BANKMASK(INTCON), INTCON_GIE_POSN    ; Genel kesmeler
    BSF BANKMASK(INTCON), INTCON_PEIE_POSN   ; Cevresel kesmeler

    ; Baslangic Degerleri Ata
    BANKSEL DESIRED_TEMP_INT
    MOVLW 25
    MOVWF BANKMASK(DESIRED_TEMP_INT)
    MOVLW 0
    MOVWF BANKMASK(DESIRED_TEMP_DEC)
    MOVLW 22
    MOVWF BANKMASK(AMBIENT_TEMP_INT)
    MOVLW 5
    MOVWF BANKMASK(AMBIENT_TEMP_DEC)
    MOVLW 15
    MOVWF BANKMASK(FAN_SPEED_RPS)

;====================================================================
; ANA DONGU
;====================================================================
LOOP:
    CALL READ_SENSOR    ; Sensoru oku
    CALL CONTROL_SYS    ; Klimayi kontrol et
    GOTO LOOP

;====================================================================
; INTERRUPT SERVISI (PC ILE HABERLESME)
;====================================================================
ISR_HANDLER:
    ; W ve STATUS yazmaclarini yedekle
    BANKSEL W_TEMP
    MOVWF BANKMASK(W_TEMP)
    SWAPF STATUS, W
    MOVWF BANKMASK(STATUS_TEMP)

    ; Veri geldigi icin mi buradayiz?
    BANKSEL PIR1
    BTFSS BANKMASK(PIR1), PIR1_RCIF_POSN
    GOTO ISR_EXIT

    ; Gelen veriyi oku
    BANKSEL RCREG
    MOVF BANKMASK(RCREG), W
    BANKSEL RX_TEMP
    MOVWF BANKMASK(RX_TEMP)

    ; --- KOMUT KONTROLU ---
    ; 1. Ortam Sicakligi Tam Sayi Iste (0x04)
    MOVLW 0x04
    SUBWF BANKMASK(RX_TEMP), W
    BTFSC STATUS, STATUS_Z_POSN
    GOTO SEND_AMB_INT

    ; 2. Ortam Sicakligi Ondalik Iste (0x03)
    MOVLW 0x03
    SUBWF BANKMASK(RX_TEMP), W
    BTFSC STATUS, STATUS_Z_POSN
    GOTO SEND_AMB_FRAC

    ; 3. Istenen Sicaklik Tam Sayi Iste (0x02)
    MOVLW 0x02
    SUBWF BANKMASK(RX_TEMP), W
    BTFSC STATUS, STATUS_Z_POSN
    GOTO SEND_DES_INT

    ; 4. Istenen Sicaklik Ondalik Iste (0x01)
    MOVLW 0x01
    SUBWF BANKMASK(RX_TEMP), W
    BTFSC STATUS, STATUS_Z_POSN
    GOTO SEND_DES_FRAC

    ; 5. Fan Hizi Iste (0x05)
    MOVLW 0x05
    SUBWF BANKMASK(RX_TEMP), W
    BTFSC STATUS, STATUS_Z_POSN
    GOTO SEND_FAN

    ; --- SET (AYARLAMA) ISLEMLERI ---
    ; Header kontrolu: 11xxxxxx (Tam Sayi Ayarla)
    MOVF BANKMASK(RX_TEMP), W
    ANDLW 0xC0
    XORLW 0xC0
    BTFSC STATUS, STATUS_Z_POSN
    GOTO SET_DES_INT

    ; Header kontrolu: 10xxxxxx (Ondalik Ayarla)
    MOVF BANKMASK(RX_TEMP), W
    ANDLW 0xC0
    XORLW 0x80
    BTFSC STATUS, STATUS_Z_POSN
    GOTO SET_DES_FRAC

    GOTO ISR_EXIT

; --- GONDERME KOMUTLARI ---
SEND_AMB_INT:
    MOVF BANKMASK(AMBIENT_TEMP_INT), W
    CALL SEND_BYTE
    GOTO ISR_EXIT

SEND_AMB_FRAC:
    MOVF BANKMASK(AMBIENT_TEMP_DEC), W
    CALL SEND_BYTE
    GOTO ISR_EXIT

SEND_DES_INT:
    MOVF BANKMASK(DESIRED_TEMP_INT), W
    CALL SEND_BYTE
    GOTO ISR_EXIT

SEND_DES_FRAC:
    MOVF BANKMASK(DESIRED_TEMP_DEC), W
    CALL SEND_BYTE
    GOTO ISR_EXIT

SEND_FAN:
    MOVF BANKMASK(FAN_SPEED_RPS), W
    CALL SEND_BYTE
    GOTO ISR_EXIT

; --- AYARLAMA KOMUTLARI ---
SET_DES_INT:
    MOVF BANKMASK(RX_TEMP), W
    ANDLW 0x3F          ; 6 bitlik veriyi al
    MOVWF BANKMASK(DESIRED_TEMP_INT)
    GOTO ISR_EXIT

SET_DES_FRAC:
    MOVF BANKMASK(RX_TEMP), W
    ANDLW 0x3F
    MOVWF BANKMASK(DESIRED_TEMP_DEC)
    GOTO ISR_EXIT

ISR_EXIT:
    ; Yedekleri geri yukle
    BANKSEL STATUS_TEMP
    SWAPF BANKMASK(STATUS_TEMP), W
    MOVWF STATUS
    SWAPF BANKMASK(W_TEMP), F
    SWAPF BANKMASK(W_TEMP), W
    RETFIE

;====================================================================
; YARDIMCI FONKSIYONLAR
;====================================================================
SEND_BYTE:
    BANKSEL TXSTA
WAIT_TX:
    BTFSS BANKMASK(TXSTA), TXSTA_TRMT_POSN   ; Gonderim bitti mi?
    GOTO WAIT_TX
    MOVWF BANKMASK(TXREG)                     ; Veriyi gonder
    RETURN

READ_SENSOR:
    ; ADC Okuma (LM35)
    BANKSEL ADCON0
    BSF BANKMASK(ADCON0), ADCON0_GO_nDONE_POSN      ; Okumayi baslat
WAIT_ADC:
    BTFSC BANKMASK(ADCON0), ADCON0_GO_nDONE_POSN    ; Bitmesini bekle
    GOTO WAIT_ADC
    
    ; Sonucu Al (ADRESH yaklasik dereceyi verir)
    MOVF BANKMASK(ADRESH), W
    BANKSEL AMBIENT_TEMP_INT
    MOVWF BANKMASK(AMBIENT_TEMP_INT)
    
    ; Test amacli: Eger sicaklik 0 okursa 22 yap (Hata onleme)
    MOVF BANKMASK(AMBIENT_TEMP_INT), F
    BTFSC STATUS, STATUS_Z_POSN
    INCF BANKMASK(AMBIENT_TEMP_INT), F
    RETURN

CONTROL_SYS:
    ; Klima Mantigi (Istenen vs Ortam)
    BANKSEL AMBIENT_TEMP_INT
    MOVF BANKMASK(AMBIENT_TEMP_INT), W
    SUBWF BANKMASK(DESIRED_TEMP_INT), W
    BTFSS STATUS, STATUS_C_POSN     ; Istenen < Ortam ise C=0 (Sogut)
    GOTO COOL_MODE
    GOTO HEAT_MODE

HEAT_MODE:
    BANKSEL PORTD
    BSF BANKMASK(PORTD), 0        ; Isitici ACIK
    BCF BANKMASK(PORTD), 1        ; Sogutucu KAPALI
    RETURN

COOL_MODE:
    BANKSEL PORTD
    BCF BANKMASK(PORTD), 0        ; Isitici KAPALI
    BSF BANKMASK(PORTD), 1        ; Sogutucu ACIK
    RETURN

END resetVec