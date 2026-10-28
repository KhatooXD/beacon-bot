<img width="1280" height="400" alt="banner" src="https://github.com/user-attachments/assets/d810e879-6326-4fdb-a363-1af626958b47" />

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10%2B-F5B83D?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/discord.py-2.4%2B-5865F2?style=for-the-badge&logo=discord&logoColor=white" alt="discord.py 2.4+">
  <img src="https://img.shields.io/badge/languages-EN%20%7C%20IT-2b2d31?style=for-the-badge" alt="Languages: EN | IT">
  <img src="https://img.shields.io/github/license/KhatooXD/beacon-bot?style=for-the-badge&color=F5B83D" alt="License">
</p>
<p align="center">
  <a href="#-features">Features</a> •
  <a href="#-commands">Commands</a> •
  <a href="#-getting-started">Getting started</a> •
  <a href="#%EF%B8%8F-configuration">Configuration</a> •
  <a href="#-deployment">Deployment</a> •
  <a href="#-translations">Translations</a>
</p>

## ✨ Features
 
### 🎫 Ticket system
- **One-click panel**: a dropdown menu posted wherever you want with `/ticket-panel`
- **Ticket types**: *General support* and *Partnership*, each one opens in its own category
- **Forms on open**: users fill in a short modal before the ticket is created, so staff get the context straight away
- **Private channels**: only the user and the staff role can see the ticket
- **Staff claim**: one click to take ownership of a ticket
- **Safe closing**: confirmation step before anything gets deleted
- **HTML transcripts**: every closed ticket is exported as a Discord-styled HTML page and posted in a log channel, with issuer, closer, opening and closing time
- **Anti-spam**: one open ticket per user
- **Restart-proof**: panels and buttons keep working after the bot restarts
### 🌍 Built to be shared
- **Multi-language**: English and Italian out of the box, add your own in a single JSON file
- **Zero storage**: nothing is saved on the server, transcripts live in Discord
- **No hardcoded IDs**: everything is configured through a `.env` file
> 🛠️ More modules are on the way, starting with automatic partnership announcements.
 
---
 
## 💬 Commands
 
| Command | Who | Description |
|---|---|---|
| `/ticket-panel` | Staff | Posts the ticket panel in the current channel |
| `/add <user>` | Staff | Adds a user to the current ticket |
| `/remove <user>` | Staff | Removes a user from the current ticket |
 
Inside every ticket you'll also find the **Claim** and **Close** buttons.
 
---
 
## 🚀 Getting started
 
### Requirements
- Python **3.10** or newer
- A Discord application with a bot user ([Developer Portal](https://discord.com/developers/applications))
### 1. Create the bot
1. Create a new application in the Developer Portal and open the **Bot** tab
2. Click **Reset Token** and copy it somewhere safe
3. Enable the **Message Content Intent** (needed for transcripts)
4. In **OAuth2 → URL Generator** select the `bot` and `applications.commands` scopes and these permissions:
   `View Channels` · `Manage Channels` · `Manage Roles` · `Send Messages` · `Embed Links` · `Attach Files` · `Read Message History`
5. Open the generated link and invite the bot to your server
> ⚠️ Make sure the bot's role is **above** the staff role, otherwise it can't set channel permissions.
 
### 2. Install
```bash
git clone https://github.com/KhatooXD/beacon-bot.git
cd beacon-bot
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```
 
### 3. Configure
```bash
cp .env.example .env
```
Fill in the values (see [Configuration](#%EF%B8%8F-configuration)), then start the bot:
```bash
python bot.py
```
You should see:
```
Synced 3 slash commands (language: en)
🔆 Beacon is online as Beacon#0000
```
 
---
 
## ⚙️ Configuration
 
All settings live in the `.env` file. Turn on **Developer Mode** in Discord (*Settings → Advanced*) to copy IDs with a right click.
 
| Variable | Required | Description |
|---|:---:|---|
| `DISCORD_TOKEN` | ✅ | Your bot token |
| `GUILD_ID` | ✅ | ID of your server |
| `STAFF_ROLE_ID` | ✅ | Role that can manage tickets |
| `SUPPORT_CATEGORY_ID` | ✅ | Category where support tickets are created |
| `PARTNERSHIP_CATEGORY_ID` | ✅ | Category where partnership tickets are created |
| `TRANSCRIPT_CHANNEL_ID` | ✅ | Channel where transcripts are posted |
| `BOT_LANGUAGE` | | `en` (default) or `it` |
| `TIMEZONE` | | Timezone used in transcripts, default `Europe/Rome` |
 
> 🔒 **Never commit your `.env` file.** It's already excluded by `.gitignore`. If your token ever leaks, reset it immediately from the Developer Portal.
 
---
 
## 🖥️ Deployment
 
Beacon is lightweight and runs comfortably on a small Linux VPS (1 GB of RAM is plenty).
To keep it online 24/7 and restart it automatically, create a systemd service:
 
```bash
sudo nano /etc/systemd/system/beacon.service
```
```ini
[Unit]
Description=Beacon Discord Bot
After=network-online.target
 
[Service]
User=YOUR_USER
WorkingDirectory=/home/YOUR_USER/beacon-bot
ExecStart=/home/YOUR_USER/beacon-bot/venv/bin/python bot.py
Restart=always
RestartSec=5
 
[Install]
WantedBy=multi-user.target
```
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now beacon
journalctl -u beacon -f        # live logs
```
 
To update:
```bash
cd ~/beacon-bot && git pull && sudo systemctl restart beacon
```
 
---
 
## 🌍 Translations
 
Every message the bot sends lives in the `locales/` folder:
 
```
locales/
├── en.json
└── it.json
```
 
To add a new language:
1. Copy `locales/en.json` to `locales/<code>.json` (e.g. `es.json`)
2. Translate the values, keeping the keys and the `{placeholders}` as they are
3. Add the code to `SUPPORTED_LANGUAGES` in `config.py`
4. Set `BOT_LANGUAGE=<code>` in your `.env`
Missing keys automatically fall back to English. Pull requests with new languages are very welcome!
 
---
 
## 📁 Project structure
 
```
beacon-bot/
├── bot.py               # entry point
├── config.py            # loads settings from .env
├── cogs/
│   └── tickets.py       # ticket system
├── utils/
│   ├── i18n.py          # translation helper
│   └── transcript.py    # HTML transcript generator
├── locales/             # translation files
└── assets/              # images used in this README
```
 
---
 
## 🤝 Contributing
 
Found a bug or have an idea? [Open an issue](https://github.com/KhatooXD/beacon-bot/issues) or send a pull request.
Please keep commit messages in English and follow the existing style (`feat:`, `fix:`, `docs:`, `chore:`).
 
---
 
## 📄 License
 
Released under the [MIT License](LICENSE).
 
<p align="center">
  Made with 🔆 by <a href="https://github.com/KhatooXD">Khatoo</a>
</p>
