from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_DEVICE_TYPE


async def async_setup(hass: HomeAssistant, config: dict):
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    device_type = entry.data.get(CONF_DEVICE_TYPE)
    platforms = []

    if device_type == "socket":
        platforms = ["switch", "sensor"]
    elif device_type == "ac":
        platforms = ["climate"]
    else:
        platforms = ["switch", "sensor", "climate"]  # fallback

    await hass.config_entries.async_forward_entry_setups(entry, platforms)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    await hass.config_entries.async_forward_entry_unload(entry, "switch")
    await hass.config_entries.async_forward_entry_unload(entry, "sensor")
    await hass.config_entries.async_forward_entry_unload(entry, "climate")
    return True
