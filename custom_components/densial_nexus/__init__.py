from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .api import DensialNexusApi
from .const import CONF_BRIDGE_TOKEN, CONF_NEXUS_URL, DOMAIN
from .coordinator import DensialNexusCoordinator


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    api = DensialNexusApi(
        entry.data[CONF_NEXUS_URL],
        entry.data[CONF_BRIDGE_TOKEN],
    )
    coordinator = DensialNexusCoordinator(hass, api)
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator: DensialNexusCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
    return await coordinator.async_shutdown()
