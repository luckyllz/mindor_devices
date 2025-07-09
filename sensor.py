import logging
import json
import re
from homeassistant.components.sensor import SensorEntity
from homeassistant.components import mqtt
from homeassistant.core import callback
from homeassistant.const import UnitOfEnergy, UnitOfPower
from .const import DOMAIN, CONF_DEVICE_ID, CONF_NAME, CONF_DEVICE_PREFIX

from .utils.json_key_message import extract_from_message

_LOGGER = logging.getLogger(__name__)

device_types = ["BPS004", "BCZ001"]


async def async_setup_entry(hass, entry, async_add_entities):
    device_id = entry.data[CONF_DEVICE_ID].lower()
    device_prefix = entry.data.get(CONF_DEVICE_PREFIX, "BCZ001")
    entities = []
    if device_prefix in device_types:
        entities.append(MindorPowerSensor(hass, entry, device_id, device_prefix))
    async_add_entities(entities)


class MindorPowerSensor(SensorEntity):
    def __init__(self, hass, entry, device_id, device_prefix):
        self._hass = hass
        self._device_id = device_id
        self._device_prefix = device_prefix
        self._name = (
            f"{entry.data.get(CONF_NAME, f'Mindor 插座 {device_id[-4:] }')} 实时功率"
        )
        self._unique_id = f"{device_id}_power"
        self._state = 0.0
        self._topic = f"/{device_prefix}/{device_id}/D1/"
        self._attr_native_unit_of_measurement = UnitOfPower.WATT
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": entry.data.get(CONF_NAME, f"Mindor 插座 {device_id[-4:] }"),
            "manufacturer": "Mindor",
            "model": "Power Socket",
        }

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def native_value(self):
        return self._state

    async def async_added_to_hass(self):
        @callback
        def message_received(msg):
            try:
                # self._state = float(msg.payload)
                power_value = extract_from_message(msg.payload)

                if power_value is not None:
                    self._state = float(power_value)
                    _LOGGER.debug(
                        "监听功率: %s (原始数据: %s)", self._state, msg.payload
                    )
                else:
                    self._state = 0
                    _LOGGER.warning("无效功率数据: %s", msg.payload)
                self.async_write_ha_state()
            except ValueError:
                _LOGGER.debug("Invalid power payload: %s", msg.payload)

        await mqtt.async_subscribe(self._hass, self._topic, message_received)
