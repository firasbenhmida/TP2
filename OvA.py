import os
import hashlib
import requests
import subprocess
import serial.tools.list_ports
import time   # ✅ ADD THIS

# ------------------------------
# USER CONFIGURATION
# ------------------------------

FIRMWARE_URL = "https://github.com/firasbenhmida/TP2/blob/main/firmware.bin"
FIRMWARE_FILE = "firmware.bin"
HASH_FILE = "firmware.hash"

CHECK_INTERVAL = 30  # seconds (you can change it)

# ------------------------------
# AUTO-INSTALL ESPTOOL IF NEEDED
# ------------------------------

def install_esptool():
    try:
        subprocess.run(["esptool.exe", "--help"], capture_output=True)
        print("✔ esptool is installed.")
    except Exception:
        print("⚠ esptool missing — installing...")
        subprocess.run(["pip", "install", "esptool"])
        print("✔ esptool installed!")


def get_esptool_path():
    try:
        result = subprocess.run(["where", "esptool.exe"], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ esptool.exe not found!")
            return None
        return result.stdout.splitlines()[0]
    except Exception:
        print("❌ Could not locate esptool.exe")
        return None


# ------------------------------
# DETECT ESP8266 COM PORT
# ------------------------------

def detect_com_port():
    ports = serial.tools.list_ports.comports()

    for port in ports:
        if "USB" in port.description or "UART" in port.description:
            print(f"✔ ESP8266 detected on {port.device}")
            return port.device

    return None


# ------------------------------
# DOWNLOAD FIRMWARE
# ------------------------------

def download_firmware():
    r = requests.get(FIRMWARE_URL)

    if r.status_code != 200:
        print("❌ Failed to download firmware!")
        return False

    with open(FIRMWARE_FILE, "wb") as f:
        f.write(r.content)

    return r.content


# ------------------------------
# HASH
# ------------------------------

def file_hash(data):
    return hashlib.sha256(data).hexdigest()


def load_last_hash():
    if not os.path.exists(HASH_FILE):
        return None
    with open(HASH_FILE, "r") as f:
        return f.read().strip()


def save_hash(h):
    with open(HASH_FILE, "w") as f:
        f.write(h)


# ------------------------------
# FLASH
# ------------------------------

def flash_firmware(esptool_path, com_port):
    cmd = [
        esptool_path,
        "--chip", "esp8266",
        "--port", com_port,
        "--baud", "460800",
        "write_flash",
        "0x00000", FIRMWARE_FILE
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    print(result.stdout)

    return result.returncode == 0


# ------------------------------
# MAIN LOOP (FIXED)
# ------------------------------

def main_loop():

    print("🚀 ESP8266 OTA Service Started")

    install_esptool()
    esptool_path = get_esptool_path()

    if not esptool_path:
        return

    while True:   # ✅ INFINITE LOOP

        print("\n🔄 Checking for updates...")

        com_port = detect_com_port()
        if not com_port:
            print("⚠ ESP8266 not connected. retrying...")
            time.sleep(CHECK_INTERVAL)
            continue

        last_hash = load_last_hash()

        try:
            r = requests.get(FIRMWARE_URL)

            if r.status_code != 200:
                print("❌ Firmware not reachable")
                time.sleep(CHECK_INTERVAL)
                continue

            new_hash = file_hash(r.content)

            print(f"🔍 Current: {last_hash}")
            print(f"🔍 New:     {new_hash}")

            if new_hash == last_hash:
                print("✔ No update needed")

            else:
                print("🔥 New firmware detected!")

                if download_firmware():
                    if flash_firmware(esptool_path, com_port):
                        save_hash(new_hash)
                        print("🎉 Update success!")

        except Exception as e:
            print("⚠ Error:", e)

        print(f"⏳ Waiting {CHECK_INTERVAL}s...\n")
        time.sleep(CHECK_INTERVAL)


# ------------------------------
# RUN
# ------------------------------

if __name__ == "__main__":
    main_loop()