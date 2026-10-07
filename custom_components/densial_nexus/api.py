from __future__ import annotations

from typing import Any

import aiohttp


class DensialNexusApi:
    def __init__(self, nexus_url: str, bridge_token: str) -> None:
        self._base_url = nexus_url.rstrip("/")
        self._token = bridge_token

    async def _post(self, payload: dict[str, Any]) -> dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }
        timeout = aiohttp.ClientTimeout(total=15)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                f"{self._base_url}/api/device-bridge",
                headers=headers,
                json=payload,
            ) as response:
                if response.status == 401:
                    raise PermissionError("Invalid or revoked Densial Nexus bridge token")
                if response.status >= 400:
                    body = await response.text()
                    raise RuntimeError(f"Densial Nexus bridge error {response.status}: {body}")
                return await response.json()

    async def poll(self) -> dict[str, Any]:
        return await self._post({"op": "poll"})

    async def register(self, devices: list[dict[str, Any]]) -> dict[str, Any]:
        return await self._post({"op": "register", "devices": devices})

    async def report_state(self, entities: list[dict[str, Any]]) -> dict[str, Any]:
        return await self._post({"op": "state", "entities": entities})

    async def ack(self, command_id: str, success: bool, error: str | None = None) -> dict[str, Any]:
        return await self._post({
            "op": "ack",
            "command_id": command_id,
            "success": success,
            "error": error,
        })
