# QR ChainAuth

QR ChainAuth is a blockchain-inspired product verification web application built with Python, Flask, and SQLite. It helps administrators register products, generate QR codes, and let users verify product details through a QR-based verification page.

The application maintains a hash-linked event history to support traceability of product-related activities.

## Features

- **Admin authentication:** Protects product management with a login.
- **Product registration:** Register products and generate QR codes.
- **QR-based verification:** Access product verification pages using generated QR codes.
- **Product status tracking:** Track sold and unsold products.
- **Hash-linked history:** Maintain an event history using previous-hash and current-hash links.
- **Dashboard:** View and manage registered products.
- **SQLite storage:** Store application data locally.
- **Responsive interface:** Flask templates with custom CSS styling.

## Technology Stack

- Python
- Flask
- SQLite
- HTML and CSS
- QR code generation with `qrcode` and Pillow

## Project Structure

```text
QR-ChainAuth/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── templates/
│   ├── base.html
│   ├── create_product.html
│   ├── dashboard.html
│   ├── history.html
│   ├── home.html
│   ├── login.html
│   ├── product_detail.html
│   ├── verify_not_found.html
│   └── verify_product.html
└── static/
    └── css/
        └── style.css
```

The SQLite database and generated QR images are created locally when needed and are excluded from Git.

## Prerequisites

- Python 3.10 or later
- pip
- Git (for version control)

## Installation and Setup (Windows)

### 1. Clone the repository

```powershell
git clone https://github.com/YOUR_USERNAME/QR-ChainAuth.git
cd QR-ChainAuth
```

If you already have the project folder, open PowerShell in that folder instead.

### 2. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```
### 4. Run the application

```powershell
python app.py
```

Open the application in your browser at:

http://127.0.0.1:5000

### 5.Admin login
username:your_admin_username
password:sjc@2026



## Notes and Limitations

- The database is stored locally; data is not automatically shared between installations.
- QR codes generated with a localhost URL are intended for use on the same computer. For access from other devices, configure an appropriate reachable base URL.
- The hash-linked history is a blockchain-inspired mechanism; it should not be interpreted as a decentralized blockchain network or as a guarantee that all tampering is impossible.
- This project is intended for learning and demonstration. Review security settings before any public deployment, and never run Flask's development server with debug mode enabled in production.

## Contributors

- Jayateja pasam
- sumith reddy anugu

Replace the contributor placeholders with the contributors' preferred names and GitHub profiles.

