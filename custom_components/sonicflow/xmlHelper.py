"""XML helper functions for SonicFlow integration."""
import xml.etree.ElementTree as ET
import logging

_LOGGER = logging.getLogger(__name__)


def getTagsAttributesToList(xml: str, tag: str) -> list:
    """Extract attributes from all tags of given name."""
    try:
        xml = xml.replace('xmlns="http://subsonic.org/restapi"', "")
        root = ET.fromstring(xml)
        tags_items = root.findall(f'.//{tag}')
        return [{attr: item.get(attr) for attr in item.keys()} for item in tags_items]
    except ET.ParseError as err:
        _LOGGER.error("Failed to parse XML: %s", err)
        return []


def getTagAttributes(xml: str, tag: str) -> dict:
    """Extract attributes from first tag of given name."""
    items = getTagsAttributesToList(xml, tag)
    return items[0] if items else {}


def getAttributes(xml: str) -> dict:
    """Extract attributes from root element."""
    try:
        root = ET.fromstring(xml)
        return {attr: root.get(attr) for attr in root.keys()}
    except ET.ParseError as err:
        _LOGGER.error("Failed to parse root XML: %s", err)
        return {}


def getTagsTexts(xml: str, tag: str) -> list[str]:
    """Extract text content from all tags of given name."""
    try:
        xml = xml.replace('xmlns="http://subsonic.org/restapi"', "")
        root = ET.fromstring(xml)
        tags_items = root.findall(f'.//{tag}')
        return [item.text for item in tags_items if item.text]
    except ET.ParseError as err:
        _LOGGER.error("Failed to parse XML for texts: %s", err)
        return []