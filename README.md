# Expense Tracker – Windows Desktop App

A Windows desktop expense tracker built with Python. The application allows users to record expenses, manage recurring fixed costs, set a global salary, and view monthly financial insights through charts.

## Features
- Add and delete expenses (amount, category, date, note)
- Fixed recurring expenses (rent, bills, subscriptions)
- Global salary tracking
- Monthly insights: income, fixed expenses, variable expenses, net balance
- Auto-updating charts:
  - Category breakdown (pie chart)
  - Daily spending trend (line chart)
  - Income vs expenses (bar chart)
- Local data persistence using SQLite
- Packaged as a Windows installer (Setup.exe)

## Tech Stack
Python, Tkinter, SQLite, Matplotlib, PyInstaller, Inno Setup

## Run Locally
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
python gui_app.py

## Windows Installer
The project includes an Inno Setup script (`installer.iss`) that builds a proper Windows installer.
The installer:
- Installs the application into Program Files
- Optionally creates a desktop shortcut
- Supports clean uninstall via Windows Apps & Features
