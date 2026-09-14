"""
Zero Trust OS Continuous Authentication Desktop Agent.
Monitors system-wide behavioral biometrics across Windows OS even when the browser is closed.
Automatically locks the workstation upon detecting an unauthorized intruder.
"""

import sys
import os
import time
import math
import ctypes
import threading
import argparse
import logging
from typing import Dict, Any, List
import requests
from pynput import keyboard, mouse

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s"
)
logger = logging.getLogger("OS_ContinuousAuthAgent")


class DesktopContinuousAuthAgent:
    """
    Background OS-level daemon tracking keystroke and mouse dynamics globally.
    Streams behavioral vectors to the FastAPI / Transformer backend and secures the OS.
    """

    def __init__(self, api_url: str, username: str, password: str, auto_lock: bool = True):
        self.api_url = api_url.rstrip("/")
        self.username = username
        self.password = password
        self.auto_lock = auto_lock

        self.token = None
        self.session_id = None
        self.is_running = False

        # Event buffers
        self.keystroke_buffer = []
        self.mouse_buffer = []
        self.buffer_lock = threading.Lock()

        # Keystroke state
        self.active_keys = {}  # key -> press_time
        self.last_release_time = None

        # Mouse state
        self.last_mouse_pos = None  # (x, y, time, speed)
        self.mouse_click_start = None

        # Telemetry counters
        self.total_keys_recorded = 0
        self.total_mouse_recorded = 0
        self.consecutive_intruder_count = 0

    def authenticate(self) -> bool:
        """Authenticate user against backend API and obtain JWT Bearer token."""
        logger.info(f"Authenticating '{self.username}' with continuous auth backend...")
        try:
            res = requests.post(
                f"{self.api_url}/auth/login",
                json={"username": self.username, "password": self.password},
                timeout=10
            )
            if res.status_code == 200:
                data = res.json()
                self.token = data["access_token"]
                logger.info("Authentication successful! JWT Token acquired.")
                return True
            else:
                logger.error(f"Login failed ({res.status_code}): {res.text}")
                return False
        except Exception as e:
            logger.error(f"Network error connecting to backend: {e}")
            return False

    def start_backend_session(self) -> bool:
        """Initialize an active tracking session on the server."""
        headers = {"Authorization": f"Bearer {self.token}"}
        try:
            res = requests.post(
                f"{self.api_url}/sessions/start",
                json={"user_agent": "Windows-Desktop-Agent/1.0", "screen_resolution": "System-Wide OS"},
                headers=headers,
                timeout=10
            )
            if res.status_code == 201:
                data = res.json()
                self.session_id = data["id"]
                logger.info(f"Continuous Authentication Session Started: {self.session_id}")
                return True
            else:
                logger.error(f"Failed to start session: {res.text}")
                return False
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return False

    def lock_workstation(self):
        """Invoke native Windows API to immediately lock the computer screen."""
        logger.warning("🚨 INTRUSION DETECTED! Executing Windows LockWorkStation()...")
        try:
            ctypes.windll.user32.LockWorkStation()
            logger.warning("🔒 Workstation locked successfully to prevent unauthorized data access.")
        except Exception as e:
            logger.error(f"Failed to lock workstation: {e}")

    # --- Global Keystroke Dynamics Listeners ---
    def on_key_press(self, key):
        if not self.is_running:
            return
        now = time.time() * 1000.0  # ms
        key_id = str(key)

        if key_id not in self.active_keys:
            self.active_keys[key_id] = now

    def on_key_release(self, key):
        if not self.is_running:
            return
        now = time.time() * 1000.0
        key_id = str(key)

        if key_id in self.active_keys:
            press_time = self.active_keys.pop(key_id)
            hold_duration = max(1.0, now - press_time)
            flight_time = max(0.0, press_time - self.last_release_time) if self.last_release_time else 50.0
            self.last_release_time = now

            # Categorize key without logging sensitive character
            key_category = "ALPHANUMERIC"
            if "shift" in key_id.lower() or "ctrl" in key_id.lower() or "alt" in key_id.lower():
                key_category = "MODIFIER"
            elif "space" in key_id.lower():
                key_category = "SPACE"
            elif "backspace" in key_id.lower() or "delete" in key_id.lower():
                key_category = "BACKSPACE"
            elif "enter" in key_id.lower():
                key_category = "ENTER"

            event = {
                "timestamp": now,
                "press_time": press_time,
                "release_time": now,
                "hold_duration": hold_duration,
                "flight_time": flight_time,
                "key_category": key_category
            }

            with self.buffer_lock:
                self.keystroke_buffer.append(event)
                self.total_keys_recorded += 1

    # --- Global Mouse Kinematics Listeners ---
    def on_mouse_move(self, x, y):
        if not self.is_running:
            return
        now = time.time() * 1000.0

        if self.last_mouse_pos:
            prev_x, prev_y, prev_time, prev_speed = self.last_mouse_pos
            dt = max(1.0, now - prev_time)
            dx = x - prev_x
            dy = y - prev_y
            distance = math.hypot(dx, dy)

            # Throttle small jitter
            if distance > 3:
                speed = distance / dt
                acceleration = (speed - prev_speed) / dt
                direction = math.atan2(dy, dx)

                event = {
                    "timestamp": now,
                    "event_type": "move",
                    "x": float(x),
                    "y": float(y),
                    "speed": float(speed),
                    "distance": float(distance),
                    "direction": float(direction),
                    "acceleration": float(acceleration),
                    "click_duration": 0.0,
                    "scroll_delta": 0.0
                }

                with self.buffer_lock:
                    self.mouse_buffer.append(event)
                    self.total_mouse_recorded += 1

                self.last_mouse_pos = (x, y, now, speed)
        else:
            self.last_mouse_pos = (x, y, now, 0.0)

    def on_mouse_click(self, x, y, button, pressed):
        if not self.is_running:
            return
        now = time.time() * 1000.0

        if pressed:
            self.mouse_click_start = now
        else:
            duration = max(1.0, now - self.mouse_click_start) if self.mouse_click_start else 50.0
            self.mouse_click_start = None

            event = {
                "timestamp": now,
                "event_type": "click",
                "x": float(x),
                "y": float(y),
                "speed": 0.0,
                "distance": 0.0,
                "direction": 0.0,
                "acceleration": 0.0,
                "click_duration": float(duration),
                "scroll_delta": 0.0
            }

            with self.buffer_lock:
                self.mouse_buffer.append(event)
                self.total_mouse_recorded += 1

    def on_mouse_scroll(self, x, y, dx, dy):
        if not self.is_running:
            return
        now = time.time() * 1000.0
        event = {
            "timestamp": now,
            "event_type": "scroll",
            "x": float(x),
            "y": float(y),
            "speed": 0.0,
            "distance": 0.0,
            "direction": 0.0,
            "acceleration": 0.0,
            "click_duration": 0.0,
            "scroll_delta": float(abs(dy))
        }
        with self.buffer_lock:
            self.mouse_buffer.append(event)
            self.total_mouse_recorded += 1

    # --- Background Dispatcher & Continuous Prediction Loop ---
    def worker_loop(self):
        """Continuously flushes telemetry batches and requests Transformer inference."""
        headers = {"Authorization": f"Bearer {self.token}"}
        eval_counter = 0

        while self.is_running:
            time.sleep(3.5)
            eval_counter += 1

            # 1. Flush buffers
            with self.buffer_lock:
                keys_to_send = list(self.keystroke_buffer)
                mouse_to_send = list(self.mouse_buffer)
                self.keystroke_buffer.clear()
                self.mouse_buffer.clear()

            if keys_to_send:
                try:
                    requests.post(
                        f"{self.api_url}/behavior/keystrokes",
                        json={"session_id": self.session_id, "events": keys_to_send},
                        headers=headers,
                        timeout=8
                    )
                except Exception as e:
                    logger.warning(f"Failed to transmit keystroke batch: {e}")

            if mouse_to_send:
                try:
                    requests.post(
                        f"{self.api_url}/behavior/mouse",
                        json={"session_id": self.session_id, "events": mouse_to_send},
                        headers=headers,
                        timeout=8
                    )
                except Exception as e:
                    logger.warning(f"Failed to transmit mouse batch: {e}")

            # 2. Trigger continuous inference every 2 cycles (~7 seconds)
            if eval_counter >= 2:
                eval_counter = 0
                try:
                    res = requests.post(
                        f"{self.api_url}/predict",
                        json={"session_id": self.session_id},
                        headers=headers,
                        timeout=8
                    )
                    if res.status_code == 200:
                        pred_data = res.json()
                        status_label = pred_data["prediction"]
                        conf = pred_data["confidence"]
                        top_features = pred_data.get("important_features", [])
                        top_feat_str = ", ".join([f"{f['feature']}: {round(f['importance']*100)}%" for f in top_features[:2]])

                        logger.info(
                            f"[CONTINUOUS VERIFICATION] Status: {status_label} | "
                            f"Confidence: {conf*100:.1f}% | "
                            f"Active Keys: {self.total_keys_recorded} | Mouse: {self.total_mouse_recorded} | "
                            f"Top Cues: {top_feat_str}"
                        )

                        # Check for Intruder
                        if status_label == "POTENTIAL INTRUDER":
                            self.consecutive_intruder_count += 1
                            logger.warning(f"⚠️ Anomaly flag {self.consecutive_intruder_count}/2")

                            # Two consecutive intruder classifications triggers immediate workstation lock
                            if self.consecutive_intruder_count >= 2:
                                if self.auto_lock:
                                    self.lock_workstation()
                                self.stop()
                                break
                        else:
                            self.consecutive_intruder_count = 0
                except Exception as e:
                    logger.warning(f"Continuous inference query note: {e}")

    def start(self):
        """Starts OS-wide continuous monitoring."""
        if not self.authenticate():
            return
        if not self.start_backend_session():
            return

        self.is_running = True
        logger.info("=" * 65)
        logger.info("  ZERO TRUST OS CONTINUOUS AUTHENTICATION DAEMON RUNNING")
        logger.info("  Monitoring: ALL Windows Applications (Word, Browser, Terminal)")
        logger.info(f"  Auto-Lock Workstation on Intrusion: {'ENABLED' if self.auto_lock else 'DISABLED'}")
        logger.info("  Press Ctrl+C to terminate agent.")
        logger.info("=" * 65)

        # Start background transmission thread
        worker_thread = threading.Thread(target=self.worker_loop, daemon=True)
        worker_thread.start()

        # Start global keyboard and mouse listeners
        with keyboard.Listener(on_press=self.on_key_press, on_release=self.on_key_release) as k_listener, \
             mouse.Listener(on_move=self.on_mouse_move, on_click=self.on_mouse_click, on_scroll=self.on_mouse_scroll) as m_listener:
            try:
                k_listener.join()
                m_listener.join()
            except KeyboardInterrupt:
                logger.info("Stopping OS Continuous Authentication Daemon...")
                self.stop()

    def stop(self):
        """Gracefully shuts down agent and closes backend session."""
        self.is_running = False
        if self.session_id and self.token:
            try:
                requests.post(
                    f"{self.api_url}/sessions/stop",
                    json={"session_id": self.session_id},
                    headers={"Authorization": f"Bearer {self.token}"},
                    timeout=5
                )
                logger.info("Session concluded on backend server.")
            except Exception:
                pass
        sys.exit(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Zero Trust OS Continuous Biometrics Daemon")
    parser.add_argument("--api-url", default="https://continuous-biometric-authenticationnn-production-4039.up.railway.app/api", help="FastAPI Backend URL")
    parser.add_argument("--username", default="santhu_01", help="Registered Subject Username")
    parser.add_argument("--password", default="Password123!", help="Account Password")
    parser.add_argument("--no-lock", action="store_true", help="Disable automatic Windows LockWorkStation()")
    args = parser.parse_args()

    agent = DesktopContinuousAuthAgent(
        api_url=args.api_url,
        username=args.username,
        password=args.password,
        auto_lock=not args.no_lock
    )
    agent.start()
