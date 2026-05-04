import asyncio
import socket
import re
import logging

from datetime import timedelta
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.core import HomeAssistant

from .const import SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class MatrixCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, host: str, port: int):
        self.host = host
        self.port = port
        self._lock = asyncio.Lock()

        super().__init__(
            hass,
            logger=_LOGGER,
            name="AVAccess Matrix",
            update_interval=timedelta(seconds=SCAN_INTERVAL),
        )

    async def _send_command(self, cmd: str) -> str:
        """Send a command over TCP and return full response."""

        def _tcp():
            with socket.create_connection((self.host, self.port), timeout=3) as sock:
                sock.sendall((cmd + "\r\n").encode())
                sock.shutdown(socket.SHUT_WR)

                chunks = []
                while True:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    chunks.append(chunk)

                return b"".join(chunks).decode(errors="ignore")

        async with self._lock:
            return await asyncio.to_thread(_tcp)

    async def async_set_route(self, output: int, input_: int):
        """Set matrix route and trigger refresh."""
        await self._send_command(f"SET SW hdmiin{input_} hdmiout{output}")

        await asyncio.sleep(1)

        await self.async_request_refresh()

    async def _async_update_data(self):
        """Fetch and parse matrix state using GET MP all."""
        raw = await self._send_command("GET MP all")

        if not raw:
            raise UpdateFailed("Empty response from matrix")

        data = {}

        for line in raw.splitlines():
            line = line.strip()

            if not line.startswith("MP"):
                continue

            # Format 1: "MP hdmiout1 in2"
            match1 = re.search(r"hdmiout(\d)\s+in(\d)", line)
            if match1:
                out, inp = match1.groups()
                data[int(out)] = int(inp)
                continue

            # Format 2: "MP hdmiin2 hdmiout1" (your device)
            match2 = re.search(r"hdmiin(\d)\s+hdmiout(\d)", line)
            if match2:
                inp, out = match2.groups()
                data[int(out)] = int(inp)
                continue

        if not data:
            raise UpdateFailed(f"No valid data in response: {raw}")

        return data
