"""Cover platform for Virtual Devices.

Simulates a positionable cover using two switches (open/close) plus an optional
stop switch. Position is estimated optimistically from elapsed time and the
configured full travel time, there is no physical position feedback.
"""

from __future__ import annotations

import asyncio
import time

from homeassistant.components.cover import ATTR_POSITION, CoverEntity, CoverEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, SERVICE_TURN_OFF, SERVICE_TURN_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_DEVICE_TYPE,
    CONF_SWITCH_CLOSE,
    CONF_SWITCH_OPEN,
    CONF_SWITCH_STOP,
    CONF_TRAVEL_TIME,
    DEVICE_TYPE_COVER,
    SWITCH_DOMAIN,
)

POSITION_OPEN = 100
POSITION_CLOSED = 0
UPDATE_INTERVAL = 0.2


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the virtual cover entity."""
    if entry.data[CONF_DEVICE_TYPE] != DEVICE_TYPE_COVER:
        return
    async_add_entities([VirtualCover(entry)])


class VirtualCover(CoverEntity):
    """A virtual cover controlled by open/close switches with simulated position."""

    _attr_should_poll = False
    _attr_supported_features = (
        CoverEntityFeature.OPEN
        | CoverEntityFeature.CLOSE
        | CoverEntityFeature.STOP
        | CoverEntityFeature.SET_POSITION
    )

    def __init__(self, entry: ConfigEntry) -> None:
        self._attr_name = entry.data[CONF_NAME]
        self._attr_unique_id = entry.entry_id
        self._switch_open: str = entry.data[CONF_SWITCH_OPEN]
        self._switch_close: str = entry.data[CONF_SWITCH_CLOSE]
        self._switch_stop: str | None = entry.data.get(CONF_SWITCH_STOP)
        self._travel_time: float = entry.data[CONF_TRAVEL_TIME]
        self._position: int | None = None
        self._is_opening = False
        self._is_closing = False
        self._move_task: asyncio.Task | None = None

    @property
    def current_cover_position(self) -> int | None:
        return self._position

    @property
    def is_closed(self) -> bool | None:
        if self._position is None:
            return None
        return self._position <= POSITION_CLOSED

    @property
    def is_opening(self) -> bool:
        return self._is_opening

    @property
    def is_closing(self) -> bool:
        return self._is_closing

    async def async_will_remove_from_hass(self) -> None:
        if self._move_task is not None:
            self._move_task.cancel()

    async def async_open_cover(self, **kwargs) -> None:
        await self._move_to_position(POSITION_OPEN)

    async def async_close_cover(self, **kwargs) -> None:
        await self._move_to_position(POSITION_CLOSED)

    async def async_set_cover_position(self, **kwargs) -> None:
        await self._move_to_position(int(kwargs[ATTR_POSITION]))

    async def async_stop_cover(self, **kwargs) -> None:
        await self._stop_movement()

    async def _turn_switch(self, entity_id: str, turn_on: bool) -> None:
        await self.hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_ON if turn_on else SERVICE_TURN_OFF,
            {"entity_id": entity_id},
            blocking=True,
        )

    async def _stop_movement(self) -> None:
        if self._move_task is not None:
            self._move_task.cancel()
            self._move_task = None
        if self._switch_stop:
            await self._turn_switch(self._switch_stop, True)
            await self._turn_switch(self._switch_stop, False)
        else:
            await self._turn_switch(self._switch_open, False)
            await self._turn_switch(self._switch_close, False)
        self._is_opening = False
        self._is_closing = False
        self.async_write_ha_state()

    async def _move_to_position(self, desired: int) -> None:
        desired = max(POSITION_CLOSED, min(POSITION_OPEN, desired))
        if self._move_task is not None:
            self._move_task.cancel()
        self._move_task = self.hass.async_create_task(self._run_move(desired))

    async def _run_move(self, desired: int) -> None:
        start = (
            self._position
            if self._position is not None
            else (POSITION_CLOSED if desired > POSITION_OPEN / 2 else POSITION_OPEN)
        )
        distance = abs(desired - start)
        if distance == 0:
            return
        duration = self._travel_time * distance / POSITION_OPEN
        moving_up = desired > start

        self._is_opening = moving_up
        self._is_closing = not moving_up
        await self._turn_switch(self._switch_open if moving_up else self._switch_close, True)
        self.async_write_ha_state()

        start_time = time.monotonic()
        try:
            while True:
                elapsed = min(time.monotonic() - start_time, duration)
                progress = elapsed / duration
                self._position = round(start + (desired - start) * progress)
                self.async_write_ha_state()
                if elapsed >= duration:
                    break
                await asyncio.sleep(UPDATE_INTERVAL)
        except asyncio.CancelledError:
            await self._turn_switch(self._switch_open, False)
            await self._turn_switch(self._switch_close, False)
            self._is_opening = False
            self._is_closing = False
            raise

        await self._turn_switch(self._switch_open, False)
        await self._turn_switch(self._switch_close, False)
        self._position = desired
        self._is_opening = False
        self._is_closing = False
        self._move_task = None
        self.async_write_ha_state()
