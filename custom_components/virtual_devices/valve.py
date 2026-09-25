"""Valve platform for Virtual Devices.

A virtual valve backed by a single switch entity. The valve's open/closed
state mirrors the controlling switch's own reported state.
"""

from __future__ import annotations

from homeassistant.components.valve import ValveEntity, ValveEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, SERVICE_TURN_OFF, SERVICE_TURN_ON, STATE_ON
from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import CONF_DEVICE_TYPE, CONF_SWITCH, DEVICE_TYPE_VALVE, SWITCH_DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the virtual valve entity."""
    if entry.data[CONF_DEVICE_TYPE] != DEVICE_TYPE_VALVE:
        return
    async_add_entities([VirtualValve(entry)])


class VirtualValve(ValveEntity):
    """A virtual valve controlled by a single switch."""

    _attr_should_poll = False
    _attr_reports_position = False
    _attr_supported_features = ValveEntityFeature.OPEN | ValveEntityFeature.CLOSE

    def __init__(self, entry: ConfigEntry) -> None:
        self._attr_name = entry.data[CONF_NAME]
        self._attr_unique_id = entry.entry_id
        self._switch: str = entry.data[CONF_SWITCH]
        self._attr_is_closed: bool | None = None

    async def async_added_to_hass(self) -> None:
        state = self.hass.states.get(self._switch)
        if state is not None:
            self._attr_is_closed = state.state != STATE_ON
        self.async_on_remove(
            async_track_state_change_event(self.hass, [self._switch], self._handle_switch_change)
        )

    @callback
    def _handle_switch_change(self, event: Event[EventStateChangedData]) -> None:
        new_state = event.data["new_state"]
        if new_state is None:
            return
        self._attr_is_closed = new_state.state != STATE_ON
        self.async_write_ha_state()

    async def async_open_valve(self) -> None:
        await self.hass.services.async_call(
            SWITCH_DOMAIN, SERVICE_TURN_ON, {"entity_id": self._switch}, blocking=True
        )

    async def async_close_valve(self) -> None:
        await self.hass.services.async_call(
            SWITCH_DOMAIN, SERVICE_TURN_OFF, {"entity_id": self._switch}, blocking=True
        )
