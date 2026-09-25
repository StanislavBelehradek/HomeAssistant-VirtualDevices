"""Light platform for Virtual Devices.

A virtual on/off-only light backed by a single switch entity. The light's
on/off state mirrors the controlling switch's own reported state.
"""

from __future__ import annotations

from homeassistant.components.light import ColorMode, LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, SERVICE_TURN_OFF, SERVICE_TURN_ON, STATE_ON
from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import CONF_DEVICE_TYPE, CONF_SWITCH, DEVICE_TYPE_LIGHT, SWITCH_DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the virtual light entity."""
    if entry.data[CONF_DEVICE_TYPE] != DEVICE_TYPE_LIGHT:
        return
    async_add_entities([VirtualLight(entry)])


class VirtualLight(LightEntity):
    """A virtual on/off light controlled by a single switch."""

    _attr_should_poll = False
    _attr_color_mode = ColorMode.ONOFF
    _attr_supported_color_modes = {ColorMode.ONOFF}

    def __init__(self, entry: ConfigEntry) -> None:
        self._attr_name = entry.data[CONF_NAME]
        self._attr_unique_id = entry.entry_id
        self._switch: str = entry.data[CONF_SWITCH]
        self._attr_is_on: bool | None = None

    async def async_added_to_hass(self) -> None:
        state = self.hass.states.get(self._switch)
        if state is not None:
            self._attr_is_on = state.state == STATE_ON
        self.async_on_remove(
            async_track_state_change_event(self.hass, [self._switch], self._handle_switch_change)
        )

    @callback
    def _handle_switch_change(self, event: Event[EventStateChangedData]) -> None:
        new_state = event.data["new_state"]
        if new_state is None:
            return
        self._attr_is_on = new_state.state == STATE_ON
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs) -> None:
        await self.hass.services.async_call(
            SWITCH_DOMAIN, SERVICE_TURN_ON, {"entity_id": self._switch}, blocking=True
        )

    async def async_turn_off(self, **kwargs) -> None:
        await self.hass.services.async_call(
            SWITCH_DOMAIN, SERVICE_TURN_OFF, {"entity_id": self._switch}, blocking=True
        )
