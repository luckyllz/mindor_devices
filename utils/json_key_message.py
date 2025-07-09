import json
import logging

_LOGGER = logging.getLogger(__name__)


def extract_from_message(message, key="power"):
    message = message.strip()
    if message.startswith("{"):
        return extract_from_json(message, key)
    return None


def extract_from_json(json_message, key):
    try:
        data = json.loads(json_message)
        return validate_key(data, key)
    except json.JSONDecodeError as e:
        _LOGGER.warning("JSON解析错误: %s", str(e))
        _LOGGER.debug("原始JSON: %s", json_message)
        return None


def validate_key(data, key):
    if key not in data:
        _LOGGER.warning(
            "警告: 数据中缺少 %s 字段。已有字段: %s", key, list(data.keys())
        )
        return None
    value = data[key]
    if isinstance(value, (dict, list)):
        _LOGGER.warning("字段 %s 的值是复杂类型: %s", key, type(value).__name__)
        return None
    return value
