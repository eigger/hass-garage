"""Config flow for the Garage integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    BooleanSelector,
    EntitySelector,
    EntitySelectorConfig,
)

from .api import GarageApi, GarageAuthError, GarageConnectionError, GarageError
from .const import (
    CONF_API_TOKEN,
    CONF_ENTITY_FUEL_LEVEL,
    CONF_ENTITY_IN_VEHICLE,
    CONF_ENTITY_LATITUDE,
    CONF_ENTITY_LONGITUDE,
    CONF_ENTITY_ODOMETER,
    CONF_ENTITY_RPM,
    CONF_ENTITY_SPEED,
    CONF_HOST,
    CONF_ONLY_WHEN_IN_VEHICLE,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class GarageConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the initial setup (host + vehicle API token) for Garage."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for the Garage host and vehicle apiToken, then validate them."""
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip().rstrip("/")
            api_token = user_input[CONF_API_TOKEN].strip()

            session = async_get_clientsession(self.hass)
            api = GarageApi(session, host, api_token)
            try:
                status = await api.async_get_status()
            except GarageAuthError:
                errors["base"] = "invalid_auth"
            except GarageConnectionError:
                errors["base"] = "cannot_connect"
            except GarageError:
                errors["base"] = "unknown"
            else:
                vehicle_id = status.get("id")
                if not vehicle_id:
                    errors["base"] = "unknown"
                else:
                    await self.async_set_unique_id(vehicle_id)
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=status.get("name") or "Garage",
                        data={CONF_HOST: host, CONF_API_TOKEN: api_token},
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Required(CONF_API_TOKEN): str,
                }
            ),
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> ConfigFlowResult:
        """Handle re-authentication when the apiToken becomes invalid."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for a new apiToken and update the entry."""
        errors: dict[str, str] = {}
        entry = self._get_reauth_entry()
        if user_input is not None:
            api_token = user_input[CONF_API_TOKEN].strip()
            session = async_get_clientsession(self.hass)
            api = GarageApi(session, entry.data[CONF_HOST], api_token)
            try:
                await api.async_get_status()
            except GarageAuthError:
                errors["base"] = "invalid_auth"
            except GarageConnectionError:
                errors["base"] = "cannot_connect"
            except GarageError:
                errors["base"] = "unknown"
            else:
                return self.async_update_reload_and_abort(
                    entry, data_updates={CONF_API_TOKEN: api_token}
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_API_TOKEN): str}),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Return the options flow handler."""
        return GarageOptionsFlow()


class GarageOptionsFlow(OptionsFlow):
    """Pick which HA entities get forwarded to Garage as telemetry.

    전부 선택 사항이다 — 비워두면 해당 필드는 Garage로 전송하지 않는다.
    """

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show/handle the entity-mapping form."""
        if user_input is not None:
            # 셀렉터를 비우면 빈 문자열이 오므로, 저장 시점에 아예 키를 제거한다.
            data = {key: value for key, value in user_input.items() if value}
            return self.async_create_entry(data=data)

        current = self.config_entry.options
        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_ENTITY_LATITUDE,
                    default=current.get(CONF_ENTITY_LATITUDE, ""),
                ): EntitySelector(
                    EntitySelectorConfig(domain=["sensor", "device_tracker"])
                ),
                vol.Optional(
                    CONF_ENTITY_LONGITUDE,
                    default=current.get(CONF_ENTITY_LONGITUDE, ""),
                ): EntitySelector(
                    EntitySelectorConfig(domain=["sensor", "device_tracker"])
                ),
                vol.Optional(
                    CONF_ENTITY_SPEED,
                    default=current.get(CONF_ENTITY_SPEED, ""),
                ): EntitySelector(EntitySelectorConfig(domain="sensor")),
                vol.Optional(
                    CONF_ENTITY_RPM,
                    default=current.get(CONF_ENTITY_RPM, ""),
                ): EntitySelector(EntitySelectorConfig(domain="sensor")),
                vol.Optional(
                    CONF_ENTITY_FUEL_LEVEL,
                    default=current.get(CONF_ENTITY_FUEL_LEVEL, ""),
                ): EntitySelector(EntitySelectorConfig(domain="sensor")),
                vol.Optional(
                    CONF_ENTITY_ODOMETER,
                    default=current.get(CONF_ENTITY_ODOMETER, ""),
                ): EntitySelector(EntitySelectorConfig(domain="sensor")),
                vol.Optional(
                    CONF_ENTITY_IN_VEHICLE,
                    default=current.get(CONF_ENTITY_IN_VEHICLE, ""),
                ): EntitySelector(
                    EntitySelectorConfig(
                        domain=["binary_sensor", "device_tracker", "sensor"]
                    )
                ),
                vol.Optional(
                    CONF_ONLY_WHEN_IN_VEHICLE,
                    default=current.get(CONF_ONLY_WHEN_IN_VEHICLE, False),
                ): BooleanSelector(),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
