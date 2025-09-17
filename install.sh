#!/usr/bin/env bash

# ===== ReconHawk Install Script =====
echo -e "\n🔥 Starting ReconHawk setup...\n"

# 1) Python venv + dependencies
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 2) Go tools install (subfinder + httpx)
if ! command -v go &>/dev/null; then
    echo "[*] Installing Go..."
    if command -v pkg &>/dev/null; then
        pkg install -y golang
    elif command -v apt &>/dev/null; then
        sudo apt install -y golang
    else
        echo "[!] Please install Go manually."
    fi
fi

export GOPATH=$HOME/go
export PATH=$PATH:$GOPATH/bin

echo "[*] Installing subfinder + httpx..."
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest

echo -e "\n✅ Setup complete!"
echo "Run: source venv/bin/activate && python3 reconhawk.py <target-domain>"
