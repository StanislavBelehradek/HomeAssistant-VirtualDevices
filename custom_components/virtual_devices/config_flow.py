"""Config flow for the Virtual Devices integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_NAME
from homeassistant.helpers import selector

from .const import (
    CONF_BINARY_SENSOR,
    CONF_DEVICE_TYPE,
    CONF_DOUBLE_CLICK_TIME,
    CONF_LONG_PRESS_TIME,
    CONF_SWITCH,
    CONF_SWITCH_CLOSE,
    CONF_SWITCH_OPEN,
    CONF_SWITCH_STOP,
    CONF_TRAVEL_TIME,
    DEFAULT_DOUBLE_CLICK_TIME,
    DEFAULT_LONG_PRESS_TIME,
    DEFAULT_TRAVEL_TIME,
    DEVICE_TYPE_BUTTON,
    DEVICE_TYPE_COVER,
    DEVICE_TYPE_LIGHT,
    DEVICE_TYPE_VALVE,
    DOMAIN,
)


def _switch_selector() -> selector.EntitySelector:
    return selector.EntitySelector(selector.EntitySelectorConfig(domain="switch"))


def _binary_sensor_selector() -> selector.EntitySelector:
    return selector.EntitySelector(selector.EntitySelectorConfig(domain="binary_sensor"))


class VirtualDevicesConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Virtual Devices."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Let the user pick which kind of virtual device to add."""
        return self.async_show_menu(
            step_id="user",
            menu_options=["cover", "valve", "light", "button"],
        )

    async def async_step_cover(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Configure a virtual cover backed by an open and a close switch."""
        if user_input is not None:
            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data={CONF_DEVICE_TYPE: DEVICE_TYPE_COVER, **user_input},
            )
        schema = vol.Schema(
            {
                vol.Required(CONF_NAME): selector.TextSelector(),
                vol.Required(CONF_SWITCH_OPEN): _switch_selector(),
                vol.Required(CONF_SWITCH_CLOSE): _switch_selector(),
                vol.Optional(CONF_SWITCH_STOP): _switch_selector(),
                vol.Required(CONF_TRAVEL_TIME, default=DEFAULT_TRAVEL_TIME): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1,
                        max=300,
                        step=0.5,
                        unit_of_measurement="s",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
            }
        )
        return self.async_show_form(step_id="cover", data_schema=schema)

    async def async_step_valve(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Configure a virtual valve backed by a single switch."""
        if user_input is not None:
            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data={CONF_DEVICE_TYPE: DEVICE_TYPE_VALVE, **user_input},
            )
        schema = vol.Schema(
            {
                vol.Required(CONF_NAME): selector.TextSelector(),
                vol.Required(CONF_SWITCH): _switch_selector(),
            }
        )
        return self.async_show_form(step_id="valve", data_schema=schema)

    async def async_step_light(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Configure a virtual on/off light backed by a single switch."""
        if user_input is not None:
            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data={CONF_DEVICE_TYPE: DEVICE_TYPE_LIGHT, **user_input},
            )
        schema = vol.Schema(
            {
                vol.Required(CONF_NAME): selector.TextSelector(),
                vol.Required(CONF_SWITCH): _switch_selector(),
            }
        )
        return self.async_show_form(step_id="light", data_schema=schema)

    async def async_step_button(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Configure a virtual button that detects click patterns on a binary sensor."""
        if user_input is not None:
            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data={CONF_DEVICE_TYPE: DEVICE_TYPE_BUTTON, **user_input},
            )
        schema = vol.Schema(
            {
                vol.Required(CONF_NAME): selector.TextSelector(),
                vol.Required(CONF_BINARY_SENSOR): _binary_sensor_selector(),
                vol.Required(CONF_LONG_PRESS_TIME, default=DEFAULT_LONG_PRESS_TIME): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=200,
                        max=10000,
                        step=100,
                        unit_of_measurement="ms",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(CONF_DOUBLE_CLICK_TIME, default=DEFAULT_DOUBLE_CLICK_TIME): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=100,
                        max=2000,
                        step=50,
                        unit_of_measurement="ms",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
            }
        )
        return self.async_show_form(step_id="button", data_schema=schema)
