from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import DensialNexusApi

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=5)


class DensialNexusCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, api: DensialNexusApi) -> None:
        self.api = api
        self.hass = hass
        self._known_entities: set[str] = set()
        self._device_map: dict[str, str] = {}

        super().__init__(
            hass,
            logger=_LOGGER,
            name="Densial Nexus",
            update_interval=SCAN_INTERVAL,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            entities = self._discover_entities()
            new_entities = [
                entity
                for entity in entities
                if entity["external_id"] not in self._known_entities
            ]
            if new_entities:
                registered = await self.api.register(new_entities)
                for device in registered.get("devices", []):
                    external_id = device.get("external_id")
                    device_id = device.get("id")
                    if external_id and device_id:
                        self._device_map[device_id] = external_id
                        self._known_entities.add(external_id)

            poll = await self.api.poll()
            for device in poll.get("devices", []):
                external_id = device.get("external_id")
                device_id = device.get("id")
                if external_id and device_id:
                    self._device_map[device_id] = external_id

            for command in poll.get("commands", []):
                await self._execute_command(command)

            await self.api.report_state(entities)
            return {"entities": entities, "commands": poll.get("commands", [])}
        except Exception as err:
            raise UpdateFailed(str(err)) from err

    def _discover_entities(self) -> list[dict[str, Any]]:
        entities: list[dict[str, Any]] = []

        for state in self.hass.states.async_all("climate"):
            attrs = state.attributes
            entities.append({
                "external_id": state.entity_id,
                "name": state.name,
                "domain": "climate",
                "state": state.state,
                "supported_features": attrs.get("supported_features"),
                "hvac_modes": attrs.get("hvac_modes", []),
                "fan_modes": attrs.get("fan_modes", []),
                "current_temperature": attrs.get("current_temperature"),
                "temperature": attrs.get("temperature"),
                "fan_mode": attrs.get("fan_mode"),
            })

        return entities

    async def _execute_command(self, command: dict[str, Any]) -> None:
        command_id = command.get("id")
        device_id = command.get("device_id")
        action = command.get("action")
        value = command.get("value")

        if not command_id or not device_id or not action:
            return

        external_id = self._device_map.get(device_id)
        if not external_id:
            await self.api.ack(command_id, False, "Unknown device")
            return

        try:
            if action == "turn_on":
                state = self.hass.states.get(external_id)
                hvac_modes = state.attributes.get("hvac_modes", []) if state else []
                target_mode = "cool" if "cool" in hvac_modes else (
                    hvac_modes[0] if hvac_modes else None
                )
                if target_mode:
                    await self.hass.services.async_call(
                        "climate",
                        "set_hvac_mode",
                        {"entity_id": external_id, "hvac_mode": target_mode},
                        blocking=True,
                    )
            elif action == "turn_off":
                await self.hass.services.async_call(
                    "climate",
                    "turn_off",
                    {"entity_id": external_id},
                    blocking=True,
                )
            elif action == "set_temperature":
                await self.hass.services.async_call(
                    "climate",
                    "set_temperature",
                    {"entity_id": external_id, "temperature": float(value)},
                    blocking=True,
                )
            elif action == "set_mode":
                await self.hass.services.async_call(
                    "climate",
                    "set_hvac_mode",
                    {"entity_id": external_id, "hvac_mode": str(value)},
                    blocking=True,
                )
            elif action == "set_fan_speed":
                await self.hass.services.async_call(
                    "climate",
                    "set_fan_mode",
                    {"entity_id": external_id, "fan_mode": str(value)},
                    blocking=True,
                )
            else:
                await self.api.ack(command_id, False, f"Unsupported action: {action}")
                return

            await self.api.ack(command_id, True)
        except Exception as err:
            await self.api.ack(command_id, False, str(err))
