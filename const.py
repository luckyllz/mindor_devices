DOMAIN = "mindor_devices"

CONF_DEVICE_ID = "device_id"
CONF_NAME = "name"

DEFAULT_NAME = "Mindor Devices"

CONF_DEVICE_PREFIX = "device_prefix"  # 新增设备主题前缀字段
CONF_DEVICE_TYPE = "device_type"  # 设备类型：socket 或 ac

# 空调模式映射
AC_MODES = [
    "auto",
    "cool",
    "heat",
    "dry",
    "fan_only",
]

# 空调风速选项
AC_FAN_MODES = [
    "auto",
    "low",
    "medium",
    "high",
]

# 扫风方向选项
AC_SWING_MODES = [
    "off",
    "vertical",
    "horizontal",
    "both",
]
