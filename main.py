import asyncio
import logging
import websockets
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from ocpp.v201 import ChargePoint as cp
from ocpp.v201 import call_result
from ocpp.v201.enums import RegistrationStatusType
import random
import string

# Setup basic logging
logging.basicConfig(level=logging.INFO)

# Function to generate a random token
def generate_token(length=10):
    characters = string.ascii_letters + string.digits
    token = ''.join(random.choice(characters) for _ in range(length))
    return token

# Simulated token list
VALID_TOKENS = {generate_token(), generate_token(), "TOKEN123"}
print(f"Generated tokens: {VALID_TOKENS}")

# OCPP ChargePoint class
class ChargePoint(cp):
    ('BootNotification')
    async def on_boot_notification(self, charging_station, reason, **kwargs):
        logging.info(f"BootNotification received: {charging_station}")
        return call_result.BootNotificationPayload(
            current_time=datetime.utcnow().isoformat(),
            interval=10,
            status=RegistrationStatusType.accepted
        )

    async def on_message(self, message):
        logging.info(f"Received message from client: {message}")
        response = f"Server received: {message}"
        await self._send(response)

# Handling client connections
async def on_connect(websocket, path):
    query_params = parse_qs(urlparse(path).query)
    token = query_params.get('token', [None])[0]

    # Token validation
    if not token or token not in VALID_TOKENS:
        logging.warning(f"Authentication failed for client. Token: {token}")
        await websocket.close(reason="Invalid or missing authentication token.")
        return

    logging.info(f"Client authenticated with token: {token}")
    await websocket.send("Welcome! You are authenticated.")

    charge_point_id = path.strip('/')
    cp = ChargePoint(charge_point_id, websocket)

    async for message in websocket:
        await cp.on_message(message)

        # Optionally send mock serial data periodically
        await send_serial_data(websocket)

# Simulate sending serial data
async def send_serial_data(websocket):
    serial_data = [
        "Data1: Voltage: 220V",
        "Data2: Current: 10A",
        "Data3: Temperature: 25C"
    ]
    for data in serial_data:
        await asyncio.sleep(2)
        await websocket.send(data)

# Main function to start the WebSocket server
async def main():
    server = await websockets.serve(on_connect, '0.0.0.0', 9000, subprotocols=['ocpp2.0.1'])
    logging.info("WebSocket Server started at ws://0.0.0.0:9000")
    await server.wait_closed()

if __name__ == '_main_':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Server stopped by user.")