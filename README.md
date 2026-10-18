# QR ChainAuth

QR ChainAuth is a blockchain-inspired product verification web application built using Python, Flask, and SQLite. It enables administrators to register products, generate QR codes, and allows users to verify product details by scanning or opening a product's QR code.

The application maintains a hash-linked event history to improve product traceability and record product-related activities.

## Features

- **Admin Authentication:** Secure login for product management.
- **Product Registration:** Register products and generate QR codes.
- **QR-Based Verification:** Verify product details using QR codes.
- **Product Status Tracking:** Track sold and unsold products.
- **Hash-Linked Event History:** Record events using previous-hash and current-hash links.
- **Dashboard:** View and manage registered products.
- **SQLite Database:** Store application data locally.
- **Responsive Interface:** User interface built with HTML, CSS, and Flask templates.

## Technology Stack

- **Backend:** Python, Flask
- **Database:** SQLite
- **Frontend:** HTML, CSS, Jinja2 templates
- **QR Code Generation:** `qrcode`, Pillow
- **Version Control:** Git and GitHub

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

The SQLite database and generated QR images are created locally when needed. They are excluded from version control.

## Prerequisites

- Python 3.10 or later
- pip
- Git

## Installation and Setup (Windows)

### 1. Clone the repository

```powershell
git clone https://github.com/saichaitanyakorrapati/QR-ChainAuth.git
cd QR-ChainAuth
```

If you already have the project folder, open PowerShell in that directory instead.

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

### 4. Configure environment variables

The application requires a secret key and administrator credentials. Set them in PowerShell before starting the application:

```powershell
$env:SECRET_KEY = python -c "import secrets; print(secrets.token_hex(32))"
$env:ADMIN_USERNAME = Read-Host "Enter an admin username"
$env:ADMIN_PASSWORD = Read-Host "Enter a strong admin password"
```

Optionally, configure the base URL used when generating QR codes:

```powershell
$env:BASE_URL = "http://127.0.0.1:5000"
```

Use your own credentials. Do not hardcode passwords or secret keys in the source code or commit them to GitHub.

**Note:** These environment variables apply to the current PowerShell session. If you open a new terminal, configure them again before starting the application.

### 5. Run the application

```powershell
python app.py
```

Open the following URL in your browser:

http://127.0.0.1:5000

Log in using the administrator username and password configured in Step 4.

## Notes and Limitations

- **Local Database:** Each installation stores its own SQLite database. Data is not automatically shared between different installations.
- **QR Code URLs:** QR codes generated with a localhost URL are intended for use on the same computer. To scan them from other devices, configure a reachable base URL and ensure the application is accessible over the network.
- **Hash-Linked History:** The application uses a blockchain-inspired, hash-linked history. It is not a decentralized blockchain network and does not guarantee that all tampering is impossible.
- **Development Use:** This project is intended for educational and demonstration purposes. Review security settings before deployment. Do not expose Flask's development server with debug mode enabled to the public internet.

## Contributors

- **Jayateja Pasam**
- **Sumith Reddy Anugu**

## License

No license has been specified yet. Add a license if you want to define how others may use, modify, and distribute this project.
