from __future__ import annotations

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_BRIDGE_TOKEN, CONF_NEXUS_URL, DEFAULT_NEXUS_URL, DOMAIN


class DensialNexusConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            url = user_input[CONF_NEXUS_URL].strip()
            token = user_input[CONF_BRIDGE_TOKEN].strip()
            session = async_get_clientsession(self.hass)

            try:
                async with session.post(
                    f"{url.rstrip('/')}/api/device-bridge",
                    headers={"Authorization": f"Bearer {token}"},
                    json={"op": "register", "devices": []},
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as response:
                    if response.status == 401:
                        errors["base"] = "invalid_token"
                    elif response.status >= 400:
                        errors["base"] = "cannot_connect"
                    else:
                        await response.json()
            except Exception:
                errors["base"] = "cannot_connect"

            if not errors:
                await self.async_set_unique_id(url)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title="Densial Nexus",
                    data={
                        CONF_NEXUS_URL: url,
                        CONF_BRIDGE_TOKEN: token,
                    },
                )

        schema = vol.Schema({
            vol.Required(CONF_NEXUS_URL, default=DEFAULT_NEXUS_URL): str,
            vol.Required(CONF_BRIDGE_TOKEN): str,
        })

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )
