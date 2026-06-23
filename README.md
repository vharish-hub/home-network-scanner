# 🛡️ Home Network Vulnerability Scanner

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-green.svg)](https://flask.palletsprojects.com)
[![React](https://img.shields.io/badge/React-18.2-61DAFB.svg)](https://reactjs.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A professional-grade web-based network vulnerability scanner that discovers devices, identifies security vulnerabilities, evaluates risk levels, and generates detailed PDF/HTML reports with remediation recommendations.

## ✨ Key Features

- **Network Discovery** — Automatically detect all devices on your network with OS fingerprinting and vendor identification
- **Port Scanning** — Quick, Full, and Custom scan modes with service version detection
- **Vulnerability Assessment** — CVE mapping with CVSS scoring and exploit availability tracking
- **Risk Analysis** — Weighted risk scoring engine with severity-based analysis
- **Interactive Dashboard** — Real-time charts, gauges, and statistics
- **Report Generation** — Professional PDF and HTML reports with executive summaries
- **Data Export** — CSV and JSON export formats
- **JWT Authentication** — Secure login with role-based access control


## LIVE DEMO:
--https://home-network-scanner-gold.vercel.app/


## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend | React 18, React-Bootstrap 5, Recharts |
| Backend | Python Flask, Flask-JWT-Extended |
| Database | SQLite (SQLAlchemy ORM) |
| Scanning | Nmap (python-nmap) |
| Reporting | ReportLab (PDF), HTML |
| Auth | JWT with bcrypt password hashing |

## 📁 Project Structure

```
home-network-scanner/
├── backend/
│   ├── app/
│   │   ├── __init__.py          # Flask app factory
│   │   ├── config.py            # Environment configurations
│   │   ├── extensions.py        # Flask extensions
│   │   ├── models/              # SQLAlchemy ORM models
│   │   ├── routes/              # API route blueprints
│   │   ├── services/            # Business logic services
│   │   └── utils/               # Decorators & helpers
│   ├── seed_data.py             # Database seeder
│   ├── requirements.txt         # Python dependencies
│   └── run.py                   # Entry point
├── frontend/
│   ├── public/                  # Static assets
│   └── src/
│       ├── components/          # Reusable UI components
│       ├── pages/               # Page components
│       ├── services/            # API service modules
│       ├── context/             # React context (Auth)
│       ├── App.jsx              # Main app component
│       └── index.css            # Design system
└── README.md
```

## Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- Nmap (optional, for live scanning)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/macOS

# Install dependencies
pip install -r requirements.txt

# Seed the database
python seed_data.py

# Start the server
python run.py
```

Backend runs at: `http://localhost:5000`

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm start
```

Frontend runs at: `http://localhost:3000` (proxied to backend)



## 📡 API Overview

| Endpoint | Description |
|----------|-------------|
| `POST /api/auth/login` | User login |
| `POST /api/auth/register` | User registration |
| `POST /api/scans/start` | Start a network scan |
| `GET /api/scans` | List all scans |
| `GET /api/devices` | List discovered devices |
| `GET /api/vulnerabilities` | List vulnerabilities |
| `GET /api/dashboard/summary` | Dashboard statistics |
| `POST /api/reports/generate/:id` | Generate report |
| `GET /api/reports/download/:file` | Download report |

## 📄 License

This project is licensed under the MIT License.
