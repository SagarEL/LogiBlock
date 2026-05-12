# LogiBlock - Blockchain-Based Secure Route Verification System

LogiBlock is an advanced, role-based logistics management system built with Flask and Python. It simulates an enterprise logistics network where shipments are tracked along mathematically authorized routes using a custom SHA-256 blockchain engine to prevent tampering and routing violations.

## Features

- **Multi-Role Architecture:** Four completely isolated web dashboards for Admins, Warehouse Staff, Delivery Agents, and Clients.
- **Secure Route Verification:** The system hashes authorized warehouse sequences. Upon package arrival, the warehouse QR scan is validated against the blockchain's expected route. 
- **Blockchain Engine:** All logistics lifecycles (`SHIPMENT_CREATED`, `WAREHOUSE_VERIFIED`, `ROUTE_ALERT`, `DELIVERY_COMPLETED`) are permanently forged as linked blocks.
- **Tamper Detection Simulation:** Includes an academic feature to corrupt data directly in the SQLite database to demonstrate how the cryptographic chain detects anomalies.
- **Real-Time Agent Navigation:** Integrated Leaflet.js maps for Delivery Agents.
- **Modern UI/UX:** Built with TailwindCSS utilizing a dynamic glassmorphism design system.

## Technology Stack

- **Backend:** Python 3, Flask, Flask-SQLAlchemy, Flask-Login
- **Database:** SQLite (V2 schema)
- **Frontend:** HTML5, TailwindCSS (CDN), FontAwesome
- **Maps:** Leaflet.js
- **Utilities:** Python `qrcode`, `hashlib`

## Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/logiblock.git
   cd logiblock
   ```

2. **Set up a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the database and seed data:**
   ```bash
   python seed_data.py
   ```

5. **Run the Flask server:**
   ```bash
   python app.py
   ```

6. **Access the Application:**
   Open your browser and navigate to `http://127.0.0.1:5000/`.

## Default Test Accounts

Please see `credentials.txt` for the pre-seeded login credentials for each of the four roles.

## Project Structure

* `app.py`: Application factory and setup.
* `blockchain.py`: Cryptographic SHA-256 ledger engine.
* `models.py`: Database schemas.
* `seed_data.py`: Data initialization script (Warehouses).
* `routes/`: Isolated blueprint routing logic for `admin`, `warehouse`, `delivery`, `user`, and `auth`.
* `templates/`: Separated base layouts and dashboard pages for each role.

## License

This project is intended for academic and demonstration purposes.
