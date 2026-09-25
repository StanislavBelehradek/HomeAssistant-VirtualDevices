"""Event platform for Virtual Devices.

A virtual button is input-only: it watches a binary_sensor and turns its
on/off transitions into single_press / double_press / long_press events.
"""

from __future__ import annotations

import time

from homeassistant.components.event import EventDeviceClass, EventEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, STATE_ON
from homeassistant.core import CALLBACK_TYPE, Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_call_later, async_track_state_change_event

from .const import (
    CONF_BINARY_SENSOR,
    CONF_DEVICE_TYPE,
    CONF_DOUBLE_CLICK_TIME,
    CONF_LONG_PRESS_TIME,
    DEVICE_TYPE_BUTTON,
)

EVENT_SINGLE_PRESS = "single_press"
EVENT_DOUBLE_PRESS = "double_press"
EVENT_LONG_PRESS = "long_press"


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the virtual button event entity."""
    if entry.data[CONF_DEVICE_TYPE] != DEVICE_TYPE_BUTTON:
        return
    async_add_entities([VirtualButtonEvent(entry)])


class VirtualButtonEvent(EventEntity):
    """Detects single/double/long press patterns from a binary_sensor's state."""

    _attr_should_poll = False
    _attr_device_class = EventDeviceClass.BUTTON
    _attr_event_types = [EVENT_SINGLE_PRESS, EVENT_DOUBLE_PRESS, EVENT_LONG_PRESS]

    def __init__(self, entry: ConfigEntry) -> None:
        self._attr_name = entry.data[CONF_NAME]
        self._attr_unique_id = entry.entry_id
        self._binary_sensor: str = entry.data[CONF_BINARY_SENSOR]
        self._long_press_s: float = entry.data[CONF_LONG_PRESS_TIME] / 1000
        self._double_click_s: float = entry.data[CONF_DOUBLE_CLICK_TIME] / 1000
        self._long_press_fired = False
        self._long_press_cancel: CALLBACK_TYPE | None = None
        self._pending_single_cancel: CALLBACK_TYPE | None = None

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_track_state_change_event(
                self.hass, [self._binary_sensor], self._handle_sensor_change
            )
        )

    @callback
    def _handle_sensor_change(self, event: Event[EventStateChangedData]) -> None:
        old_state = event.data["old_state"]
        new_state = event.data["new_state"]
        if new_state is None or old_state is None:
            return
        if new_state.state == STATE_ON and old_state.state != STATE_ON:
            self._on_press()
        elif new_state.state != STATE_ON and old_state.state == STATE_ON:
            self._on_release()

    @callback
    def _on_press(self) -> None:
        self._long_press_fired = False
        self._long_press_cancel = async_call_later(self.hass, self._long_press_s, self._fire_long_press)

    @callback
    def _fire_long_press(self, _now: float) -> None:
        self._long_press_cancel = None
        self._long_press_fired = True
        self._trigger_event(EVENT_LONG_PRESS)
        self.async_write_ha_state()

    @callback
    def _on_release(self) -> None:
        if self._long_press_cancel is not None:
            self._long_press_cancel()
            self._long_press_cancel = None
        if self._long_press_fired:
            return
        if self._pending_single_cancel is not None:
            self._pending_single_cancel()
            self._pending_single_cancel = None
            self._trigger_event(EVENT_DOUBLE_PRESS)
            self.async_write_ha_state()
            return
        self._pending_single_cancel = async_call_later(
            self.hass, self._double_click_s, self._fire_single_press
        )

    @callback
    def _fire_single_press(self, _now: float) -> None:
        self._pending_single_cancel = None
        self._trigger_event(EVENT_SINGLE_PRESS)
        self.async_write_ha_state()
