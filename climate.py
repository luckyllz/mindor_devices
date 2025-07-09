import logging
import json
import asyncio

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    ClimateEntityFeature,
    HVACMode,
    FAN_AUTO,
)
from homeassistant.const import UnitOfTemperature
from homeassistant.core import callback
from homeassistant.components import mqtt
from .const import (
    DOMAIN,
    CONF_DEVICE_ID,
    CONF_NAME,
    CONF_DEVICE_PREFIX,
    CONF_DEVICE_TYPE,
)
from .utils.json_key_message import extract_from_message

_LOGGER = logging.getLogger(__name__)

SUPPORTED_HVAC_MODES = [
    HVACMode.OFF,
    HVACMode.COOL,
    HVACMode.HEAT,
    HVACMode.DRY,
    HVACMode.FAN_ONLY,
    HVACMode.AUTO,
]

SUPPORTED_FAN_MODES = ["low", "medium", "high", FAN_AUTO]
SUPPORTED_SWING_MODES = ["off", "vertical", "horizontal"]


async def async_setup_entry(hass, entry, async_add_entities):
    if entry.data.get(CONF_DEVICE_TYPE) != "ac":
        return  # 非空调类型，不添加空调实体
    device_id = entry.data[CONF_DEVICE_ID].lower()
    device_prefix = entry.data.get(CONF_DEVICE_PREFIX, "XCZ006")
    async_add_entities([MindorClimate(hass, entry, device_id, device_prefix)])


def temp_to_hex(temp):
    # 步骤1：十进制转两位十六进制
    hex_temp = hex(temp)[2:].upper().zfill(2)
    # 步骤2：十六进制加法
    hex_check = hex(int(hex_temp, 16) + 0x52)[2:].upper().zfill(2)
    return f"{hex_temp},{hex_check},"


class MindorClimate(ClimateEntity):
    _attr_temperature_unit = "°C"
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.FAN_MODE
        | ClimateEntityFeature.SWING_MODE
    )
    _attr_max_temp = 30
    _attr_min_temp = 16
    _attr_target_temperature_step = 1  # 👈 这里是新增的

    def __init__(self, hass, entry, device_id, device_prefix):
        self._hass = hass
        self._device_id = device_id
        self._prefix = device_prefix
        self._name = entry.data.get(CONF_NAME, f"Mindor 空调伴侣 {device_id[-4:]}")
        self._unique_id = f"{device_id}_climate"
        self._state_topic = f"/{device_prefix}/{device_id}/D1/"
        self._command_topic = f"/{device_prefix}/{device_id}/C1/"

        self._hvac_mode = HVACMode.OFF
        self._target_temp = 26
        self._fan_mode = FAN_AUTO
        self._swing_mode = "off"
        self._display_on = True

        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": self._name,
            "manufacturer": "Mindor",
            "model": "AC Companion",
        }
        self.acSwitch = False

    @property
    def name(self):
        return self._name

    @property
    def is_on(self):
        return self._hvac_mode != HVACMode.OFF

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def hvac_mode(self):
        return self._hvac_mode

    @property
    def hvac_modes(self):
        return SUPPORTED_HVAC_MODES

    @property
    def target_temperature(self):
        return self._target_temp

    @property
    def fan_mode(self):
        return self._fan_mode

    @property
    def fan_modes(self):
        return SUPPORTED_FAN_MODES

    @property
    def swing_mode(self):
        return self._swing_mode

    @property
    def swing_modes(self):
        return SUPPORTED_SWING_MODES

    async def async_set_hvac_mode(self, hvac_mode):
        self._hvac_mode = hvac_mode
        mode_map = {
            HVACMode.COOL: "01,4F,",  # 制冷
            HVACMode.HEAT: "02,50,",  # 制热
            HVACMode.DRY: "03,51,",  # 除湿
            HVACMode.FAN_ONLY: "04,52,",  # 送风
            HVACMode.AUTO: "00,4E,",  # 自动
        }
        if hvac_mode == HVACMode.OFF:
            self.acSwitch = False
            await mqtt.async_publish(
                self._hass,
                self._command_topic,
                "WY+CI1302=FN:A5,9A,02,07,00,00,03,02,00,00,4D,",
            )
            return
        if self.acSwitch == False:
            self.acSwitch = True
            await mqtt.async_publish(
                self._hass,
                self._command_topic,
                "WY+CI1302=FN:A5,9A,02,07,00,00,03,02,00,01,4E,",
            )
            await asyncio.sleep(0.5)
        if hvac_mode in mode_map:
            await mqtt.async_publish(
                self._hass,
                self._command_topic,
                f"WY+CI1302=FN:A5,9A,02,07,00,00,03,02,01,{mode_map[hvac_mode]}",
            )
        # pattern 0 自动 4 送风 3 除湿 2 制热 1 制冷

        # 2
        # WY+CI1302=FN:A5,9A,02,07,00,00,03,02,01,02,50,
        # 1
        # WY+CI1302=FN:A5,9A,02,07,00,00,03,02,01,01,4F,
        # 0
        # WY+CI1302=FN:A5,9A,02,07,00,00,03,02,01,00,4E,
        # 3
        # WY+CI1302=FN:A5,9A,02,07,00,00,03,02,01,03,51,
        # 4
        # WY+CI1302=FN:A5,9A,02,07,00,00,03,02,01,04,52,

        # await self._send_command()

    async def async_set_temperature(self, **kwargs):
        temperature = kwargs.get("temperature")
        if temperature:
            self._target_temp = int(temperature)
            hex_temp = temp_to_hex(self._target_temp)
            _LOGGER.debug(f"设置温度: {self._target_temp}")
            _LOGGER.debug(
                f"设置温度: WY+CI1302=FN:A5,9A,02,07,00,00,03,02,05,{hex_temp}"
            )

            await mqtt.async_publish(
                self._hass,
                self._command_topic,
                f"WY+CI1302=FN:A5,9A,02,07,00,00,03,02,05,{hex_temp}",
            )

    async def async_set_fan_mode(self, fan_mode):
        self._fan_mode = fan_mode
        map_fan_mode = {
            FAN_AUTO: "02,51,",  # 自动
            "low": "01,50,",  # 低
            "medium": "04,53,",  # 中
            "high": "03,52,",  # 高
        }
        if fan_mode in map_fan_mode:
            await mqtt.async_publish(
                self._hass,
                self._command_topic,
                f"WY+CI1302=FN:A5,9A,02,07,00,00,03,02,02,{map_fan_mode[fan_mode]}",
            )

        #         WY+CI1302=FN:A5,9A,02,07,00,00,03,02,02,02,51, //自动 2
        # WY+CI1302=FN:A5,9A,02,07,00,00,03,02,02,01,50,, //低速 1
        # WY+CI1302=FN:A5,9A,02,07,00,00,03,02,02,04,53, // 中速 4
        # WY+CI1302=FN:A5,9A,02,07,00,00,03,02,02,03,52, // 高速 3

        #     wind_speed

    async def async_set_swing_mode(self, swing_mode):
        self._swing_mode = swing_mode
        map_swing_mode = {
            "off": "00,50,",  # 关闭
            "vertical": "01,51,",  # 垂直
            "horizontal": "03,53,",  # 水平
        }
        if swing_mode in map_swing_mode:
            await mqtt.async_publish(
                self._hass,
                self._command_topic,
                f"WY+CI1302=FN:A5,9A,02,07,00,00,03,02,03,{map_swing_mode[swing_mode]}",
            )

    #             WY+CI1302=FN:A5,9A,02,07,00,00,03,02,03,01,51, // 上下 1
    # WY+CI1302=FN:A5,9A,02,07,00,00,03,02,03,03,53, // 左右 3
    # WY+CI1302=FN:A5,9A,02,07,00,00,03,02,03,00,50,  //关闭

    # sweeping_state
    # await self._send_command()

    async def _send_command(self):
        payload = {
            "power": 1 if self._hvac_mode != HVACMode.OFF else 0,
            "mode": self._hvac_mode,
            "temp": self._target_temp,
            "fan": self._fan_mode,
            "swing": self._swing_mode,
            "display": 1 if self._display_on else 0,
        }
        await mqtt.async_publish(self._hass, self._command_topic, json.dumps(payload))
        _LOGGER.debug("Sent AC command: %s", payload)

    async def async_added_to_hass(self):
        @callback
        def handle_state(msg):
            try:
                # 解析消息
                # 开关
                switch_value = extract_from_message(msg.payload, "switch")
                if switch_value is not None:
                    self.acSwitch = switch_value == 1

                # 模式
                pattern_value = extract_from_message(msg.payload, "pattern")
                if pattern_value is not None:
                    pattern_value = int(pattern_value)
                    if pattern_value == 0:
                        self._hvac_mode = HVACMode.AUTO
                    elif pattern_value == 1:
                        self._hvac_mode = HVACMode.COOL
                    elif pattern_value == 2:
                        self._hvac_mode = HVACMode.HEAT
                    elif pattern_value == 3:
                        self._hvac_mode = HVACMode.DRY
                    elif pattern_value == 4:
                        self._hvac_mode = HVACMode.FAN_ONLY

                # 温度
                temp_value = extract_from_message(msg.payload, "temperature")
                _LOGGER.debug("温度: %s", temp_value)
                if temp_value is not None:
                    self._target_temp = int(temp_value)

                # 风速
                fan_value = extract_from_message(msg.payload, "wind_speed")
                if fan_value is not None:
                    fan_value = int(fan_value)
                    if fan_value == 2:
                        self._fan_mode = FAN_AUTO
                    elif fan_value == 1:
                        self._fan_mode = "low"
                    elif fan_value == 4:
                        self._fan_mode = "medium"
                    elif fan_value == 3:
                        self._fan_mode = "high"
                # 上下摆风
                swing_value = extract_from_message(msg.payload, "sweeping_state")
                if swing_value is not None:
                    swing_value = int(swing_value)
                    if swing_value == 1:
                        self._swing_mode = "vertical"
                    elif swing_value == 3:
                        self._swing_mode = "horizontal"
                    elif swing_value == 0:
                        self._swing_mode = "off"

                # data = json.loads(msg.payload)
                # self._hvac_mode = data.get("mode", self._hvac_mode)
                # self._target_temp = data.get("temp", self._target_temp)
                # self._fan_mode = data.get("fan", self._fan_mode)
                # self._swing_mode = data.get("swing", self._swing_mode)
                # self._display_on = data.get("display", 1) == 1
                self.async_write_ha_state()
                # _LOGGER.debug("Received AC state update: %s", data)
            except Exception as e:
                _LOGGER.warning("Error parsing AC state: %s", e)

        await mqtt.async_subscribe(self._hass, self._state_topic, handle_state)
