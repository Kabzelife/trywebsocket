import asyncio
import websockets
import json
import mysql.connector
import os
from mysql.connector import pooling
from aiohttp import web
import logging
import random

# Logging konfigurieren
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Port für den Webserver
port = int(os.getenv('PORT', 5000))

# MySQL-Verbindungs-Pooling konfigurieren
dbconfig = {
    "host": os.getenv('DB_HOST', "92.205.233.38"),
    "user": os.getenv('DB_USER', "gaijin"),
    "password": os.getenv('DB_PASSWORD', "D@v!s19942021"),
    "database": os.getenv('DB_DATABASE', "admin_fetch")
}

# Erstellen des Verbindungspools
connection_pool = pooling.MySQLConnectionPool(
    pool_name="mypool",
    pool_size=32,  # Erhöhte Poolgröße
    **dbconfig
)

websocket_instance = None

async def subscribe():
    global websocket_instance
    if websocket_instance is not None:
        await websocket_instance.close()  # Sicherstellen, dass die alte Verbindung geschlossen wird
        websocket_instance = None

    uri = "wss://pumpportal.fun/api/data"
    max_retries = 10
    retry_count = 0
    while retry_count < max_retries:
        try:
            websocket_instance = await websockets.connect(uri, ping_interval=20, close_timeout=10)
            logger.info("🔗 WebSocket verbunden")

            # Abonnieren für neue Tokens
            await websocket_instance.send(json.dumps({"method": "subscribeNewToken"}))
            logger.info("✅ Anfrage 'subscribeNewToken' gesendet")

            # Abonniere bestehende Tokens und Entwickler
            await subscribe_existing_tokens_and_devs(websocket_instance)

            # Empfang und Verarbeitung der Daten
            try:
                async for message in websocket_instance:
                    logger.info(f"📩 Nachricht empfangen: {message}")
                    data = json.loads(message)
                    await process_data(data)
            finally:
                # Sicherstellen, dass die Verbindung korrekt geschlossen wird
                if websocket_instance:
                    await websocket_instance.close()
                    websocket_instance = None
                    logger.info("WebSocket geschlossen")

        except websockets.exceptions.ConnectionClosedError as e:
            retry_count += 1
            backoff_time = min(60, (2 ** retry_count) + random.uniform(0, 1))
            logger.warning(f"❌ Verbindung geschlossen: {e}. Neuer Versuch in {backoff_time} Sekunden...")
            await asyncio.sleep(backoff_time)
        except Exception as e:
            logger.error(f"❌ Unerwarteter Fehler: {e}")
            await asyncio.sleep(5)
    else:
        logger.error("Maximale Anzahl an Verbindungsversuchen erreicht. Beende Task.")


async def subscribe_existing_tokens_and_devs(websocket):
    """
    Abonniert bestehende Tokens und Entwickler nur einmal.
    """
    tokens = fetch_all_tokens()
    devs = fetch_all_devs()

    if tokens:
        logger.info(f"📊 Abonniere bestehende Tokens: {len(tokens)}")
        for token in tokens:
            try:
                await websocket.send(json.dumps({
                    "method": "subscribeTokenTrade",
                    "keys": [token["mint"]]
                }))
                logger.info(f"📦 Abonniert: {token['mint']}")
            except Exception as e:
                logger.error(f"❌ Fehler beim Abonnement von {token['mint']}: {e}")
    else:
        logger.warning("⚠️ Keine Tokens zum Abonnieren gefunden.")

    if devs:
        logger.info(f"📊 Abonniere Entwicklerkonten: {len(devs)}")
        for dev in devs:
            try:
                await websocket.send(json.dumps({
                    "method": "subscribeAccountTrade",
                    "keys": [dev["public_key"]]
                }))
                logger.info(f"📦 Abonniert: {dev['public_key']}")
            except Exception as e:
                logger.error(f"❌ Fehler beim Abonnement von Entwickler {dev['public_key']}: {e}")
    else:
        logger.warning("⚠️ Keine Entwickler zum Abonnieren gefunden.")


def fetch_all_tokens():
    """
    Ruft alle Tokens aus der Datenbank ab und gibt sie als Liste von Dictionaries zurück.
    """
    try:
        db_connection = connection_pool.get_connection()
        cursor = db_connection.cursor(dictionary=True)
        cursor.execute("SELECT mint FROM tokens")
        tokens = cursor.fetchall()
        cursor.close()
        db_connection.close()

        if tokens:
            logger.info(f"🔍 Tokens abgerufen: {len(tokens)}")
        else:
            logger.warning("⚠️ Keine Tokens in der Datenbank gefunden.")

        return tokens
    except Exception as e:
        logger.error(f"❌ Fehler beim Abrufen der Tokens: {e}")
        return []

def fetch_all_devs():
    """
    Ruft alle Entwickler aus der Datenbank ab und gibt sie als Liste von Dictionaries zurück.
    """
    try:
        db_connection = connection_pool.get_connection()
        cursor = db_connection.cursor(dictionary=True)
        cursor.execute("SELECT public_key FROM developers")
        devs = cursor.fetchall()
        cursor.close()
        db_connection.close()

        if devs:
            logger.info(f"🔍 Entwickler abgerufen: {len(devs)}")
        else:
            logger.warning("⚠️ Keine Entwickler in der Datenbank gefunden.")

        return devs
    except Exception as e:
        logger.error(f"❌ Fehler beim Abrufen der Entwickler: {e}")
        return []

async def process_data(data):
    """
    Verarbeitet empfangene Daten vom WebSocket.
    """
    if "mint" in data:
        logger.info(f"Token {data['mint']} empfangen")

        if data.get("txType") == "create":
            await save_to_tokens(data)
            await save_dev_info(data)
        elif "marketCapSol" in data:  # Überprüfen, ob 'marketCapSol' in den Daten existiert
            logger.info(f"📊 Update für Token {data['mint']} empfangen")
            await save_to_token_updates(data)
            await check_dev_activity(data)
        else:
            logger.info(f"Unbekannter Datentyp, überspringe: {data}")


async def save_to_tokens(data):
    try:
        db_connection = connection_pool.get_connection()
        cursor = db_connection.cursor()
        cursor.execute("""
            INSERT IGNORE INTO tokens (signature, mint, traderPublicKey, txType, initialBuy, solAmount, bondingCurveKey, 
                                        vTokensInBondingCurve, vSolInBondingCurve, marketCapSol, name, symbol, uri, pool, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """, (
            data.get("signature"),
            data.get("mint"),
            data.get("traderPublicKey"),
            data.get("txType"),
            data.get("initialBuy"),
            data.get("solAmount"),
            data.get("bondingCurveKey"),
            data.get("vTokensInBondingCurve"),
            data.get("vSolInBondingCurve"),
            data.get("marketCapSol"),
            data.get("name"),
            data.get("symbol"),
            data.get("uri"),
            data.get("pool")
        ))
        db_connection.commit()
        logger.info(f"Neues Token gespeichert: {data.get('mint')}")
    except Exception as e:
        logger.error(f"Fehler beim Speichern in tokens: {e}")
    finally:
        if db_connection:
            db_connection.close()

async def save_to_token_updates(data):
    try:
        db_connection = connection_pool.get_connection()
        cursor = db_connection.cursor()
        cursor.execute("""
            INSERT INTO token_updates (mint, traderPublicKey, txType, solAmount, vTokensInBondingCurve, vSolInBondingCurve, marketCapSol, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            ON DUPLICATE KEY UPDATE
                traderPublicKey = VALUES(traderPublicKey),
                txType = VALUES(txType),
                solAmount = VALUES(solAmount),
                vTokensInBondingCurve = VALUES(vTokensInBondingCurve),
                vSolInBondingCurve = VALUES(vSolInBondingCurve),
                marketCapSol = VALUES(marketCapSol),
                updated_at = NOW()
        """, (
            data.get("mint"),
            data.get("traderPublicKey"),
            data.get("txType"),
            data.get("solAmount"),
            data.get("vTokensInBondingCurve"),
            data.get("vSolInBondingCurve"),
            data.get("marketCapSol")
        ))
        # Hier wird kein fetch benötigt, da es sich um ein INSERT handelt.
        db_connection.commit()
        logger.info(f"Update für Token gespeichert: {data.get('mint')}")
    except Exception as e:
        logger.error(f"Fehler beim Speichern der token_updates: {e}")
    finally:
        if 'cursor' in locals():  # Überprüfen, ob cursor definiert ist, bevor wir es schließen
            cursor.close()
        if db_connection:
            db_connection.close()

async def check_dev_activity(data):
    try:
        db_connection = connection_pool.get_connection()
        cursor = db_connection.cursor()
        cursor.execute("SELECT traderPublicKey, solAmount FROM tokens WHERE mint = %s", (data.get("mint"),))
        token_info = cursor.fetchone()
        
        # Schließe den Cursor direkt nach fetchone
        cursor.close()

        if token_info:
            dev_public_key, dev_sol_amount = token_info  # Entwicklerdaten abrufen

            # Prüfen, ob der Entwickler an diesem Trade beteiligt ist
            if data.get("traderPublicKey") == dev_public_key:
                tx_type = data.get("txType")
                update_sol_amount = data.get("solAmount")

                action = None
                if tx_type == "sell":
                    if dev_sol_amount <= update_sol_amount:
                        action = "Developer sold all"
                    else:
                        action = f"Developer sold part: {update_sol_amount} of {dev_sol_amount}"
                elif tx_type == "buy":
                    action = f"Developer bought more: {update_sol_amount} SOL"

                if action:
                    # Für jede neue SQL-Operation einen neuen Cursor öffnen
                    cursor = db_connection.cursor()
                    cursor.execute("""
                        INSERT INTO DEV_TOKEN_HOLDING (mint, traderPublicKey, txType, solAmount, initialBuy, action, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, NOW())
                    """, (
                        data.get("mint"),
                        dev_public_key,
                        tx_type,
                        update_sol_amount,
                        dev_sol_amount,
                        action
                    ))
                    db_connection.commit()
                    cursor.close()  # Schließe den Cursor nach der Operation
                    logger.info(f"Entwickleraktivität gespeichert: {action}")
    except Exception as e:
        logger.error(f"Fehler beim Überprüfen der Entwickleraktivität: {e}")
    finally:
        if db_connection:
            db_connection.close()

async def save_dev_info(data):
    db_connection = None
    cursor = None
    try:
        db_connection = connection_pool.get_connection()
        cursor = db_connection.cursor()

        # Prüfen, ob der Entwickler schon in der Datenbank existiert
        cursor.execute("SELECT id FROM developers WHERE public_key = %s", (data.get("traderPublicKey"),))
        result = cursor.fetchone()

        if not result:
            cursor.execute(
                "INSERT INTO developers (public_key, first_seen_at) VALUES (%s, NOW())",
                (data.get("traderPublicKey"),)
            )
            db_connection.commit()
            logger.info(f"Entwicklerinformationen gespeichert: {data.get('traderPublicKey')}")

    except Exception as e:
        logger.error(f"Fehler beim Speichern der Entwicklerinformationen: {e}")
    finally:
        if cursor:
            cursor.close()
        if db_connection:
            db_connection.close()



async def periodic_marketcap_validation():
    while True:
        try:
            tokens = fetch_all_tokens()
            for token in tokens:
                latest_update = await fetch_latest_update(token['mint'])
                if latest_update and 'marketCapSol' in latest_update:
                    if latest_update['marketCapSol'] != token['marketCapSol']:
                        await update_token_marketcap(token['mint'], latest_update['marketCapSol'])
                else:
                    logger.warning(f"Keine MarketCapSol Daten für Token {token['mint']}")
        except Exception as e:
            logger.error(f"Fehler bei der periodischen MarketCap-Validierung: {e}")
        finally:
            await asyncio.sleep(1)

async def fetch_latest_update(mint):
    try:
        db_connection = connection_pool.get_connection()
        cursor = db_connection.cursor(dictionary=True)
        cursor.execute("SELECT marketCapSol FROM token_updates WHERE mint = %s ORDER BY updated_at DESC LIMIT 1", (mint,))
        update = cursor.fetchone()
        cursor.close()
        db_connection.close()
        return update
    except Exception as e:
        logger.error(f"Fehler beim Abrufen des neuesten Updates für {mint}: {e}")
        return None


async def update_token_marketcap(mint, marketCapSol):
    try:
        db_connection = connection_pool.get_connection()
        cursor = db_connection.cursor()
        cursor.execute("UPDATE tokens SET marketCapSol = %s WHERE mint = %s", (marketCapSol, mint))
        db_connection.commit()
        cursor.close()
        db_connection.close()
        logger.info(f"MarketCap aktualisiert für Token {mint}: {marketCapSol}")
    except Exception as e:
        logger.error(f"Fehler beim Aktualisieren der MarketCap für {mint}: {e}")

async def clean_old_data():
    """Löscht Tokens und zugehörige Updates, die älter als eine Stunde sind, aber nicht die Entwicklerinfo."""
    while True:
        try:
            logger.info("🧹 Starte Bereinigung alter Daten...")
            db_connection = connection_pool.get_connection()
            cursor = db_connection.cursor()

            # Tokens löschen, die älter als 1 Stunde sind
            cursor.execute("""
                DELETE FROM tokens WHERE created_at < NOW() - INTERVAL 1 HOUR
            """)
            deleted_tokens = cursor.rowcount
            logger.info(f"🗑️ Gelöschte Tokens: {deleted_tokens}")

            # Verwaiste token_updates löschen
            cursor.execute("""
                DELETE FROM token_updates WHERE mint NOT IN (SELECT mint FROM tokens)
            """)
            deleted_updates = cursor.rowcount
            logger.info(f"🗑️ Gelöschte Updates: {deleted_updates}")

            # Entwickleraktivitäten löschen, die älter als 1 Stunde sind, aber nicht die Entwickler selbst
            cursor.execute("""
                DELETE FROM DEV_TOKEN_HOLDING WHERE created_at < NOW() - INTERVAL 1 HOUR
            """)
            deleted_dev_activities = cursor.rowcount
            logger.info(f"🗑️ Gelöschte Entwickleraktivitäten: {deleted_dev_activities}")

            db_connection.commit()
            cursor.close()
            db_connection.close()
        except Exception as e:
            logger.error(f"❌ Fehler beim Bereinigen der alten Daten: {e}")
        finally:
            await asyncio.sleep(60)  # Warte 1 Minute, bevor die nächste Bereinigung startet

async def clear_all_data_on_start():
    """
    Löscht alle Daten in den Tabellen tokens, token_updates und DEV_TOKEN_HOLDING bei Serverstart.
    """
    try:
        db_connection = connection_pool.get_connection()
        cursor = db_connection.cursor()

        # Alle Daten aus den Tabellen löschen
        cursor.execute("DELETE FROM tokens")
        cursor.execute("DELETE FROM token_updates")
        cursor.execute("DELETE FROM DEV_TOKEN_HOLDING")

        db_connection.commit()
        cursor.close()
        logger.info("Alle alten Daten wurden bei Serverstart aus den Tabellen gelöscht.")
    except Exception as e:
        logger.error(f"Fehler beim Löschen aller Daten bei Serverstart: {e}")
    finally:
        if db_connection:
            db_connection.close()

async def on_start(request):
    return web.Response(text="WebSocket-Server läuft!")

async def main():
    """
    Startet den WebSocket-Listener, HTTP-Server und periodische Aufgaben.
    """
    # Löscht alle Daten bei Serverstart
    await clear_all_data_on_start()

    app = web.Application()
    app.router.add_get('/', on_start)

    asyncio.create_task(subscribe())
    asyncio.create_task(clean_old_data())

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

    logger.info(f"Server läuft auf Port {port}")
    
    try:
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        logger.info("WebSocket Listener wurde gestoppt")

if __name__ == "__main__":
    asyncio.run(main())
