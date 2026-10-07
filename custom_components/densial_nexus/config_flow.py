from __future__ import annotations

import logging

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_BRIDGE_TOKEN, CONF_NEXUS_URL, DEFAULT_NEXUS_URL, DOMAIN

_LOGGER = logging.getLogger(__name__)


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
                    response_body = await response.text()

                    if response.status == 401:
                        errors["base"] = "invalid_token"
                        _LOGGER.error(
                            "Densial Nexus bridge rejected the token with HTTP 401: %s",
                            response_body,
                        )
                    elif response.status >= 400:
                        errors["base"] = "cannot_connect"
                        _LOGGER.error(
                            "Densial Nexus bridge returned HTTP %s: %s",
                            response.status,
                            response_body,
                        )
                    else:
                        try:
                            await response.json(content_type=None)
                        except Exception:
                            _LOGGER.debug(
                                "Densial Nexus bridge returned a non-JSON success response: %s",
                                response_body,
                            )
                        _LOGGER.info(
                            "Densial Nexus bridge registration succeeded for %s",
                            url,
                        )
            except aiohttp.ClientError as err:
                errors["base"] = "cannot_connect"
                _LOGGER.error(
                    "Could not reach Densial Nexus bridge at %s: %s",
                    url,
                    err,
                )
            except Exception:
                errors["base"] = "cannot_connect"
                _LOGGER.exception(
                    "Unexpected error while connecting to Densial Nexus bridge at %s",
                    url,
                )

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
