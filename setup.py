import os
import subprocess
import sys
import time

def setup_virtualenv():
    if not sys.platform.startswith("win"):
        print("Этот скрипт предназначен только для Windows!")
        sys.exit()

    venv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".venv")
    
    if not os.path.exists(venv_path):
        print("Создание виртуальной среды...")
        subprocess.call([sys.executable, "-m", "venv", ".venv"], shell=True)
    else:
        print("Виртуальная среда уже существует!")

    python_path = os.path.join(venv_path, "Scripts", "python.exe" if sys.platform.startswith("win") else "bin/python")
    pip_path = os.path.join(venv_path, "Scripts", "pip.exe" if sys.platform.startswith("win") else "bin/pip")

    print("Обновление pip в виртуальной среде...")
    try:
        subprocess.call([python_path, "-m", "pip", "install", "--upgrade", "pip"], shell=True)
        print("Pip успешно обновлён!")
    except Exception as e:
        print(f"Ошибка при обновлении pip: {e}")
        print("Продолжаем с текущей версией pip...")

    required_packages = [
        "requests",
        "beautifulsoup4",
        "customtkinter"
    ]

    print("Установка зависимостей в виртуальной среде...")
    for package in required_packages:
        try:
            subprocess.call([pip_path, "install", package], shell=True)
            print(f"Установлен пакет: {package}")
        except Exception as e:
            print(f"Ошибка установки {package}: {e}")
            sys.exit()
    time.sleep(5)

if __name__ == "__main__":
    setup_virtualenv()