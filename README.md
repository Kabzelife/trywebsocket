**WebSocket Listener for PumpPortal.fun**

This WebSocket listener is designed to interact with **Pump.fun**, specifically to monitor and update data for newly created tokens in real-time. Below are the key features and instructions for implementation:

### Features
1. **Real-Time Subscription**:
   - The listener subscribes to updates for all newly created tokens on **Pump.fun**.
   - It monitors live buy and sell activities, dynamically updating the market capitalization.

2. **Database Management**:
   - A dedicated database will be created to store relevant information.
   - The database will include:
     - All newly created tokens.
     - Market capitalization updates.
     - Developer wallet addresses.

3. **Automated Data Cleanup**:
   - Tokens older than **1 hour** will be permanently deleted from the database, along with their associated updates.

4. **Developer Monitoring**:
   - Developer wallet addresses will be stored in the database.
   - Updates will include actions such as:
     - Token sales.
     - Partial sales (e.g., selling half of the tokens).
     - Token purchases.

### Setup Instructions
1. **Python Installation**:
   - Ensure Python is installed on your system. You can download it from the [official Python website](https://www.python.org/downloads/).

2. **Virtual Environment**:
   - Create a virtual environment to manage dependencies:
     ```bash
     python -m venv venv
     source venv/bin/activate  # For Linux/macOS
     venv\Scripts\activate   # For Windows
     ```

3. **Start the WebSocket Listener**:
   - Save the script as `WebSocket_Listener.py`.
   - Install required dependencies (if any) using `pip install -r requirements.txt`.
   - Run the script:
     ```bash
     python WebSocket_Listener.py
     ```

4. **Enjoy the Service**:
   - The listener will automatically handle subscription, updates, and database management.

This WebSocket listener provides an efficient way to monitor token activity on Pump.fun while ensuring clean and up-to-date data storage.


Tabelle tokens:<br>
sql<p>
<B>
```bash
CREATE TABLE tokens (<br>
    signature VARCHAR(255),<br>
    mint VARCHAR(255),<br>
    traderPublicKey VARCHAR(255),<br>
    txType VARCHAR(50),<br>
    initialBuy DECIMAL(18, 9),<br>
    solAmount DECIMAL(18, 9),<br>
    bondingCurveKey VARCHAR(255),<br>
    vTokensInBondingCurve DECIMAL(18, 9),<br>
    vSolInBondingCurve DECIMAL(18, 9),<br>
    marketCapSol DECIMAL(18, 9),<br>
    name VARCHAR(255),<br>
    symbol VARCHAR(50),<br>
    uri VARCHAR(255),<br>
    pool VARCHAR(255),<br>
    created_at DATETIME,<br>
    PRIMARY KEY (mint)<br>
);<p>
```
Tabelle token_updates:<br>
sql<p>
```bash
CREATE TABLE token_updates (<br>
    id INT AUTO_INCREMENT PRIMARY KEY,<br>
    mint VARCHAR(255),<br>
    traderPublicKey VARCHAR(255),<br>
    txType VARCHAR(50),<br>
    solAmount DECIMAL(18, 9),<br>
    vTokensInBondingCurve DECIMAL(18, 9),<br>
    vSolInBondingCurve DECIMAL(18, 9),<br>
    marketCapSol DECIMAL(18, 9),<br>
    updated_at DATETIME,<br>
    INDEX idx_mint (mint)<br>
);<p>
```
Tabelle developers:<br>
sql<p>
```bash
CREATE TABLE developers (<br>
    id INT AUTO_INCREMENT PRIMARY KEY,<br>
    public_key VARCHAR(255) UNIQUE,<br>
    first_seen_at DATETIME<br>
);<p>
```
Tabelle DEV_TOKEN_HOLDING:<br>
sql<p>
```bash
CREATE TABLE DEV_TOKEN_HOLDING (<br>
    id INT AUTO_INCREMENT PRIMARY KEY,<br>
    mint VARCHAR(255),<br>
    traderPublicKey VARCHAR(255),<br>
    txType VARCHAR(50),<br>
    solAmount DECIMAL(18, 9),<br>
    initialBuy DECIMAL(18, 9),<br>
    action VARCHAR(255),<br>
    created_at DATETIME,<br>
    INDEX idx_mint (mint)<br>
);<p>
</b>
```
