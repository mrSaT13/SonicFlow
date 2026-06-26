"""Robust XML parser for Subsonic/Navidrome API."""
import xml.etree.ElementTree as ET
import logging

_LOGGER = logging.getLogger(__name__)

def _strip_ns(xml_str: str) -> str:
    """Remove namespace to simplify XPath queries."""
    return xml_str.replace('xmlns="http://subsonic.org/restapi"', "") if xml_str else ""

def parse_root(xml_str: str) -> ET.Element | None:
    """Parse XML string safely."""
    try:
        return ET.fromstring(_strip_ns(xml_str))
    except ET.ParseError as e:
        _LOGGER.error("XML parse error: %s", e)
        return None

def get_root_attrs(xml_str: str) -> dict:
    """Get attributes of <subsonic-response> root."""
    root = parse_root(xml_str)
    return root.attrib if root is not None else {}

def find_elements(xml_str: str, tag: str) -> list[ET.Element]:
    """Find all elements by tag name."""
    root = parse_root(xml_str)
    return root.findall(f".//{tag}") if root is not None else []

def get_first_element(xml_str: str, tag: str) -> ET.Element | None:
    """Get first matching element."""
    elements = find_elements(xml_str, tag)
    return elements[0] if elements else None

def elements_to_dicts(xml_str: str, tag: str) -> list[dict]:
    """Convert XML elements to list of dicts with all attributes."""
    return [el.attrib for el in find_elements(xml_str, tag)]

def element_to_dict(xml_str: str, tag: str) -> dict:
    """Convert first matching element to dict."""
    el = get_first_element(xml_str, tag)
    return el.attrib if el is not None else {}

def elements_to_texts(xml_str: str, tag: str) -> list[str]:
    """Extract text content from elements."""
    return [el.text for el in find_elements(xml_str, tag) if el.text]


# Aliases for backward compatibility with subsonicApi.py
def getAttributes(xml_str: str) -> dict:
    """Alias for get_root_attrs."""
    return get_root_attrs(xml_str)

def getTagAttributes(xml_str: str, tag: str) -> dict:
    """Alias for element_to_dict."""
    return element_to_dict(xml_str, tag)

def getTagsAttributesToList(xml_str: str, tag: str) -> list[dict]:
    """Alias for elements_to_dicts."""
    return elements_to_dicts(xml_str, tag)

def getTagsTexts(xml_str: str, tag: str) -> list[str]:
    """Alias for elements_to_texts."""
    return elements_to_texts(xml_str, tag)
