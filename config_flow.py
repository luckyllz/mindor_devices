import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import DOMAIN, CONF_DEVICE_ID, CONF_NAME, CONF_DEVICE_PREFIX, CONF_DEVICE_TYPE

DEVICE_TYPES = {
    "socket": "插座",
    "ac": "空调伴侣",
}

DEVICE_PREFIXES = [
    "BCZ001",
    "XCZ006",
]

class MindorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self):
        self._device_id = None
        self._device_name = None
        self._device_prefix = None
        self._device_type = None

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            self._device_id = user_input[CONF_DEVICE_ID].strip()
            self._device_name = user_input.get(CONF_NAME) or f"Mindor设备 {self._device_id[-4:]}"
            self._device_prefix = user_input[CONF_DEVICE_PREFIX]
            self._device_type = user_input[CONF_DEVICE_TYPE]

            return self.async_create_entry(
                title=self._device_name,
                data={
                    CONF_DEVICE_ID: self._device_id,
                    CONF_NAME: self._device_name,
                    CONF_DEVICE_PREFIX: self._device_prefix,
                    CONF_DEVICE_TYPE: self._device_type,
                },
            )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_DEVICE_ID): str,
                vol.Optional(CONF_NAME, default=""): str,
                vol.Required(CONF_DEVICE_PREFIX, default="BCZ001"): str,
                vol.Required(CONF_DEVICE_TYPE, default="socket"): vol.In(list(DEVICE_TYPES.keys())),
            }
        )

        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)

    @classmethod
    @callback
    def async_get_options_flow(cls, config_entry):
        return MindorOptionsFlowHandler(config_entry)


class MindorOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        errors = {}

        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        data_schema = vol.Schema(
            {
                vol.Required(CONF_DEVICE_ID, default=self.config_entry.data.get(CONF_DEVICE_ID)): str,
                vol.Optional(CONF_NAME, default=self.config_entry.data.get(CONF_NAME, "")): str,
                vol.Optional(CONF_DEVICE_PREFIX, default=self.config_entry.data.get(CONF_DEVICE_PREFIX, "BCZ001")): str,
                vol.Required(CONF_DEVICE_TYPE, default=self.config_entry.data.get(CONF_DEVICE_TYPE, "socket")): vol.In(list(DEVICE_TYPES.keys())),
            }
        )

        return self.async_show_form(step_id="init", data_schema=data_schema, errors=errors)
