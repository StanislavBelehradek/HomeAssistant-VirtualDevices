"""The Virtual Devices integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import (
    CONF_DEVICE_TYPE,
    DEVICE_TYPE_BUTTON,
    DEVICE_TYPE_COVER,
    DEVICE_TYPE_LIGHT,
    DEVICE_TYPE_VALVE,
    DOMAIN,
)

# Each config entry represents a single virtual device of one of these types.
PLATFORMS_BY_TYPE: dict[str, list[Platform]] = {
    DEVICE_TYPE_COVER: [Platform.COVER],
    DEVICE_TYPE_VALVE: [Platform.VALVE],
    DEVICE_TYPE_LIGHT: [Platform.LIGHT],
    DEVICE_TYPE_BUTTON: [Platform.EVENT],
}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Virtual Devices from a config entry."""
    device_type = entry.data[CONF_DEVICE_TYPE]
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = entry.data
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS_BY_TYPE[device_type])
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    device_type = entry.data[CONF_DEVICE_TYPE]
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS_BY_TYPE[device_type])
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
