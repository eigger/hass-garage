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
from homeassistant.helpers.selector import EntitySelector, EntitySelectorConfig

from .api import GarageApi, GarageAuthError, GarageConnectionError, GarageError
from .const import (
    CONF_API_TOKEN,
    CONF_ENTITY_LOCATION,
    CONF_ENTITY_RPM,
    CONF_HOST,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class GarageConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the initial setup (host + vehicle API token) for Garage."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._host: str | None = None
        self._api_token: str | None = None
        self._title: str | None = None

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
                    self._host = host
                    self._api_token = api_token
                    self._title = status.get("name") or "Garage"
                    return await self.async_step_sensors()

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

    async def async_step_sensors(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Step 2: Pick which HA entities get forwarded to Garage as telemetry."""
        if user_input is not None:
            data = {key: value for key, value in user_input.items() if value}
            return self.async_create_entry(
                title=self._title or "Garage",
                data={CONF_HOST: self._host, CONF_API_TOKEN: self._api_token},
                options=data,
            )

        return self.async_show_form(
            step_id="sensors",
            data_schema=_sensor_options_schema(),
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


def _sensor_options_schema(current: dict[str, Any] | None = None) -> vol.Schema:
    """Build entity selector schema for sensor mapping.

    위치는 device_tracker 하나로만 받는다 — HA의 device_tracker는 이미
    latitude/longitude를 속성으로 들고 있는 표준 "위치" 엔티티라, 위도/경도를 각각
    고를 필요가 없다(plain sensor는 위경도 두 값을 동시에 담을 수 없어 애초에
    이 용도에 맞지 않는다).
    """
    if current is None:
        current = {}
    return vol.Schema(
        {
            vol.Optional(
                CONF_ENTITY_LOCATION,
                default=current.get(CONF_ENTITY_LOCATION, ""),
            ): EntitySelector(EntitySelectorConfig(domain="device_tracker")),
            vol.Optional(
                CONF_ENTITY_RPM,
                default=current.get(CONF_ENTITY_RPM, ""),
            ): EntitySelector(EntitySelectorConfig(domain="sensor")),
        }
    )


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
        return self.async_show_form(
            step_id="init", data_schema=_sensor_options_schema(current)
        )
