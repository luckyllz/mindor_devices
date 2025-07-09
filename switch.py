import logging
from homeassistant.components.switch import SwitchEntity
from homeassistant.components import mqtt
from homeassistant.core import callback
from .const import DOMAIN, CONF_DEVICE_ID, CONF_NAME, CONF_DEVICE_PREFIX

from .utils.json_key_message import extract_from_message


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    device_id = entry.data[CONF_DEVICE_ID].lower()
    device_prefix = entry.data.get(CONF_DEVICE_PREFIX, "BCZ001")
    async_add_entities([MindorSwitch(hass, entry, device_id, device_prefix)])


class MindorSwitch(SwitchEntity):
    def __init__(self, hass, entry, device_id, device_prefix):
        self._hass = hass
        self._device_id = device_id
        self._device_prefix = device_prefix
        self._name = entry.data.get(CONF_NAME, f"Mindor 插座 {device_id[-4:]}")
        self._unique_id = f"{device_id}_switch"
        self._state = False
        self._command_topic = f"/{device_prefix}/{device_id}/C1/"
        self._state_topic = f"/{device_prefix}/{device_id}/D1/"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": self._name,
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
    def is_on(self):
        return self._state

    async def async_turn_on(self, **kwargs):
        if self._device_prefix == "BPS004":
            await mqtt.async_publish(
                self._hass,
                self._command_topic,
                "WY+CI1302=FN:A5,9A,02,07,00,00,03,02,00,01,4E,",
            )
        else:
            await mqtt.async_publish(self._hass, self._command_topic, "WY+SWITCH=1")
        self._state = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        if self._device_prefix == "BPS004":
            await mqtt.async_publish(
                self._hass,
                self._command_topic,
                "WY+CI1302=FN:A5,9A,02,07,00,00,03,02,00,00,4D,",
            )
        else:
            await mqtt.async_publish(self._hass, self._command_topic, "WY+SWITCH=0")
        self._state = False
        self.async_write_ha_state()

    async def async_added_to_hass(self):
        @callback
        def message_received(msg):
            payload_msg = extract_from_message(msg.payload, "switch")

            if msg.payload == "+SW:1":
                self._state = True
            elif msg.payload == "+SW:0":
                self._state = False
            elif payload_msg == 1:
                self._state = True
            elif payload_msg == 0:
                self._state = False
            self.async_write_ha_state()

        await mqtt.async_subscribe(self._hass, self._state_topic, message_received)
