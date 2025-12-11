#!/bin/bash
# script to setup on Oracle Cloud Free Tier

echo "🚀 إعداد Oracle Cloud..."

# Update system
sudo apt update
sudo apt upgrade -y

# Install Python and pip
sudo apt install python3 python3-pip git -y

# Clone repository
git clone https://github.com/yourusername/telegram-bot.git
cd telegram-bot

# Install requirements
pip3 install -r requirements.txt

# Create systemd service
sudo tee /etc/systemd/system/telegram-bot.service << EOF
[Unit]
Description=Telegram ID Card Bot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PWD
Environment="TELEGRAM_TOKEN=your_token_here"
Environment="GEMINI_API_KEY=your_key_here"
Environment="ORACLE=true"
ExecStart=/usr/bin/python3 $PWD/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
sudo systemctl daemon-reload
sudo systemctl start telegram-bot
sudo systemctl enable telegram-bot

echo "✅ تم الإعداد بنجاح!"
echo "📊 حالة الخدمة: sudo systemctl status telegram-bot"
