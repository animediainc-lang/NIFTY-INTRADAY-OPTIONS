from typing import Callable, Dict, Any, List, Optional
from data.breeze_client import breeze_client
from logger import logger
import time
import threading

class WebSocketManager:
    def __init__(self):
        self.callbacks: List[Callable[[Dict[str, Any]], None]] = []
        self.is_running = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.subscriptions: List[Dict[str, Any]] = []

    def on_ticks(self, data: Dict[str, Any]):
        """Callback for receiving ticks from Breeze SDK."""
        for callback in self.callbacks:
            try:
                callback(data)
            except Exception as e:
                logger.error(f"Error in WebSocket callback: {e}")

    def add_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Adds a callback to process incoming ticks."""
        self.callbacks.append(callback)

    def connect(self):
        """Connects to the Breeze WebSocket and sets up the tick handler."""
        try:
            breeze_client._initialize_sdk()
            breeze_client.breeze.ws_connect()
            breeze_client.breeze.on_ticks = self.on_ticks
            self.is_running = True
            self.reconnect_attempts = 0
            logger.info("Breeze WebSocket connected.")

            # Resubscribe to existing instruments if reconnecting
            for sub in self.subscriptions:
                self.subscribe(**sub, store_sub=False)

        except Exception as e:
            logger.error(f"Failed to connect to Breeze WebSocket: {e}")
            self.is_running = False
            self._handle_reconnect()

    def _handle_reconnect(self):
        """Handles reconnection with exponential backoff."""
        if self.reconnect_attempts < self.max_reconnect_attempts:
            self.reconnect_attempts += 1
            wait_time = min(2 ** self.reconnect_attempts, 30)
            logger.info(f"Attempting WebSocket reconnection in {wait_time}s (Attempt {self.reconnect_attempts}/{self.max_reconnect_attempts})")
            threading.Timer(wait_time, self.connect).start()
        else:
            logger.critical("Max WebSocket reconnection attempts reached.")

    def subscribe(self, store_sub: bool = True, **kwargs):
        """Subscribes to real-time updates for a specific instrument."""
        if store_sub:
            self.subscriptions.append(kwargs)

        try:
            breeze_client.breeze.subscribe_feeds(**kwargs)
            logger.info(f"Subscribed to {kwargs.get('stock_code')}")
        except Exception as e:
            logger.error(f"Failed to subscribe to {kwargs.get('stock_code')}: {e}")

    def disconnect(self):
        """Disconnects from the WebSocket."""
        try:
            breeze_client.breeze.ws_disconnect()
            self.is_running = False
            logger.info("Breeze WebSocket disconnected.")
        except Exception as e:
            logger.error(f"Error during WebSocket disconnect: {e}")

# Global WebSocket manager
ws_manager = WebSocketManager()
