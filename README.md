Hello there,

this is a websocket_listener for pumpportal.fun.
It will subscribe to new tokens created on pump.fun and will update the Marketcap with live sell and buy.
The information will be saved in a database wich you have to create.

All coins older then 1 hour, will be permanantly deleted from the database aswell as the updates.

All tokens will recieve a Update for Marketcap or if the dev did sell, sell half or bought tokens.
All dev's wallet addresses will be saved in the database aswell.

Install python and make a virtual envoirment.
Start the Websocket_listener.py and enjoy.

Tabelle tokens:<br>
sql<p>
<B>
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

Tabelle token_updates:<br>
sql<p>
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

Tabelle developers:<br>
sql<p>
CREATE TABLE developers (<br>
    id INT AUTO_INCREMENT PRIMARY KEY,<br>
    public_key VARCHAR(255) UNIQUE,<br>
    first_seen_at DATETIME<br>
);<p>

Tabelle DEV_TOKEN_HOLDING:<br>
sql<p>
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

