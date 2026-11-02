import json
import re
import threading
from pathlib import Path

import webview

from voicemeeter_sdk import VoicemeeterClient, VoicemeeterError


ROOT = Path(__file__).parent


class VoicemeeterApi:
    """Methods exposed to JavaScript by PyWebView."""

    def __init__(self):
        self._client = None
        self._lock = threading.RLock()
        self._connected = False

    def _state(self, message=""):
        if not self._connected or self._client is None:
            return {"connected": False, "message": message or "Disconnected"}
        try:
            version = ".".join(map(str, self._client.get_voicemeeter_version()))
            return {
                "connected": True,
                "message": message or "Connected",
                "type": self._client.get_voicemeeter_type(),
                "version": version,
            }
        except VoicemeeterError as exc:
            return {"connected": False, "message": str(exc)}

    def connect(self):
        with self._lock:
            if self._connected:
                return self._state()
            try:
                self._client = VoicemeeterClient()
                login_result = self._client.login()
                self._connected = True
                message = "Connected" if login_result == 0 else "Connected; Voicemeeter was started"
                return self._state(message)
            except (VoicemeeterError, OSError) as exc:
                self._client = None
                self._connected = False
                return self._state(str(exc))

    def disconnect(self):
        with self._lock:
            if self._client is not None and self._connected:
                try:
                    self._client.logout()
                except VoicemeeterError:
                    pass
            self._client = None
            self._connected = False
            return self._state("Disconnected")

    def status(self):
        with self._lock:
            return self._state()

    def get_parameter(self, parameter_name):
        with self._lock:
            if not self._connected:
                return {"ok": False, "error": "Connect to Voicemeeter first"}
            try:
                return {"ok": True, "name": parameter_name, "value": self._client.get_parameter_float(parameter_name)}
            except VoicemeeterError as exc:
                return {"ok": False, "error": str(exc), "name": parameter_name}

    def set_parameter(self, parameter_name, value):
        with self._lock:
            if not self._connected:
                return {"ok": False, "error": "Connect to Voicemeeter first"}
            try:
                self._client.set_parameter_float(parameter_name, float(value))
                return {"ok": True, "name": parameter_name, "value": float(value)}
            except (ValueError, VoicemeeterError) as exc:
                return {"ok": False, "error": str(exc), "name": parameter_name}

    def set_linked_parameters(self, parameter_values):
        with self._lock:
            if not self._connected:
                return {"ok": False, "error": "Connect to Voicemeeter first"}
            if not isinstance(parameter_values, list) or not 2 <= len(parameter_values) <= 8:
                return {"ok": False, "error": "Invalid linked parameter values"}
            try:
                script = []
                for item in parameter_values:
                    if not isinstance(item, dict):
                        return {"ok": False, "error": "Invalid parameter value"}
                    name = item.get("name")
                    if not isinstance(name, str) or not name:
                        return {"ok": False, "error": "Invalid parameter name"}
                    if not re.fullmatch(r"(Strip|Bus)\[\d+\]\.Gain", name):
                        return {"ok": False, "error": "Only strip and bus gain parameters can be linked"}
                    value = max(-60.0, min(12.0, float(item["value"])))
                    script.append(f"{name}={value:.6f}")
                self._client.set_parameters(";".join(script))
                return {"ok": True, "message": "Linked gains updated"}
            except (KeyError, TypeError, ValueError, VoicemeeterError) as exc:
                return {"ok": False, "error": str(exc)}

    def execute_script(self, script):
        with self._lock:
            if not self._connected:
                return {"ok": False, "error": "Connect to Voicemeeter first"}
            try:
                self._client.set_parameters(script)
                return {"ok": True, "message": "Script sent to Voicemeeter"}
            except VoicemeeterError as exc:
                return {"ok": False, "error": str(exc)}


def main():
    api = VoicemeeterApi()
    webview.create_window(
        "Voicemeeter Control",
        (ROOT / "web" / "index.html").as_uri(),
        js_api=api,
        width=1440,
        height=920,
        min_size=(960, 640),
        background_color="#0d1117",
    )
    webview.start(debug=False)
    api.disconnect()


if __name__ == "__main__":
    main()