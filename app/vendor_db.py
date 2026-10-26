"""
OUI MAC Vendor prefix database for friendly device identification.
"""

OUI_PREFIXES = {
    # Ubiquiti
    "a8:9c:6c": "Ubiquiti",
    "dc:9f:db": "Ubiquiti",
    "b4:fb:e4": "Ubiquiti",
    "24:5a:4c": "Ubiquiti",
    "78:8a:20": "Ubiquiti",
    "e0:63:da": "Ubiquiti",
    "f0:9f:c2": "Ubiquiti",
    "68:d7:9a": "Ubiquiti",
    "ac:8b:a9": "Ubiquiti",

    # Apple
    "00:17:88": "Philips Lighting (Hue)",
    "00:03:93": "Apple",
    "00:05:02": "Apple",
    "00:0a:27": "Apple",
    "00:0a:95": "Apple",
    "00:10:fa": "Apple",
    "00:11:24": "Apple",
    "00:14:51": "Apple",
    "00:16:cb": "Apple",
    "00:17:f2": "Apple",
    "00:19:e3": "Apple",
    "00:1b:63": "Apple",
    "00:1c:b3": "Apple",
    "00:1d:4f": "Apple",
    "00:1e:52": "Apple",
    "00:1e:c2": "Apple",
    "00:1f:5b": "Apple",
    "00:1f:f3": "Apple",
    "00:21:e9": "Apple",
    "00:22:41": "Apple",
    "00:23:12": "Apple",
    "00:23:32": "Apple",
    "00:23:6c": "Apple",
    "00:24:36": "Apple",
    "00:25:00": "Apple",
    "00:25:4b": "Apple",
    "00:25:bc": "Apple",
    "00:26:08": "Apple",
    "00:26:4a": "Apple",
    "00:26:b0": "Apple",
    "00:26:bb": "Apple",
    "08:9d:f4": "Apple",
    "f4:03:2a": "Apple",
    "fc:45:c3": "Apple",
    "fc:e9:d8": "Apple",
    "f0:81:73": "Apple",
    "b0:09:da": "Apple",
    "28:ea:0b": "Apple",
    "0c:47:c9": "Apple",

    # Ring / Amazon
    "9c:76:13": "Ring / Amazon",
    "44:65:0d": "Amazon Technologies",
    "74:c2:46": "Amazon Technologies",
    "ac:63:be": "Amazon Technologies",
    "fc:a6:67": "Amazon Technologies",
    "40:b4:cd": "Amazon Technologies",
    "68:37:e9": "Amazon Technologies",
    "38:f7:3d": "Amazon Technologies",
    "50:dc:e7": "Amazon Technologies",

    # Espressif / IoT (e.g. TRMNL, Home Automation)
    "b0:a6:04": "Espressif (TRMNL/IoT)",
    "24:0a:c4": "Espressif Systems",
    "30:ae:a4": "Espressif Systems",
    "24:6f:28": "Espressif Systems",
    "a4:cf:12": "Espressif Systems",
    "84:f3:eb": "Espressif Systems",
    "cc:50:e3": "Espressif Systems",
    "48:55:19": "Espressif Systems",

    # Samsung
    "00:07:ab": "Samsung",
    "00:12:47": "Samsung",
    "00:15:99": "Samsung",
    "00:16:32": "Samsung",
    "00:17:d5": "Samsung",
    "00:18:af": "Samsung",
    "00:1a:8a": "Samsung",
    "00:1b:98": "Samsung",
    "00:1c:43": "Samsung",
    "00:1d:25": "Samsung",
    "00:1e:7d": "Samsung",
    "00:21:19": "Samsung",
    "00:23:d6": "Samsung",
    "00:24:54": "Samsung",
    "00:26:5d": "Samsung",
    "50:85:69": "Samsung",
    "b8:57:d8": "Samsung",
    "bc:44:86": "Samsung",

    # Google / Nest
    "00:1a:11": "Google",
    "3c:5a:37": "Google",
    "54:60:09": "Google",
    "64:16:66": "Google Nest",
    "d8:6c:63": "Google Nest",
    "f4:03:43": "Google Nest",
    "f8:0f:f9": "Google Nest",

    # Sony / PlayStation
    "00:04:1f": "Sony",
    "00:13:15": "Sony PlayStation",
    "00:15:c1": "Sony PlayStation",
    "00:19:c5": "Sony PlayStation",
    "00:1d:0d": "Sony PlayStation",
    "00:24:8d": "Sony PlayStation",
    "28:0d:fc": "Sony PlayStation",
    "70:9e:29": "Sony PlayStation",
    "a8:e3:ee": "Sony PlayStation",

    # Microsoft / Xbox
    "00:0d:3a": "Microsoft",
    "00:12:5a": "Microsoft Xbox",
    "00:17:fa": "Microsoft Xbox",
    "00:22:48": "Microsoft Xbox",
    "28:18:78": "Microsoft Xbox",
    "7c:1e:52": "Microsoft Xbox",

    # Nintendo
    "00:09:bf": "Nintendo",
    "00:17:ab": "Nintendo",
    "00:19:1d": "Nintendo Switch",
    "00:1b:ea": "Nintendo Switch",
    "00:1f:32": "Nintendo Switch",
    "00:21:47": "Nintendo Switch",
    "00:22:aa": "Nintendo Switch",
    "00:23:cc": "Nintendo Switch",
    "00:24:44": "Nintendo Switch",
    "00:25:a0": "Nintendo Switch",
    "00:26:59": "Nintendo Switch",
    "98:b6:e9": "Nintendo Switch",

    # TP-Link
    "00:27:19": "TP-Link",
    "14:cc:20": "TP-Link",
    "50:c7:bf": "TP-Link",
    "60:e3:27": "TP-Link",
    "98:48:27": "TP-Link",
    "b0:4e:26": "TP-Link",

    # Raspberry Pi
    "b8:27:eb": "Raspberry Pi",
    "dc:a6:32": "Raspberry Pi",
    "e4:5f:01": "Raspberry Pi",
    "28:cd:c1": "Raspberry Pi",

    # Intel
    "00:1b:21": "Intel",
    "00:1e:67": "Intel",
    "00:21:6a": "Intel",
    "00:22:fb": "Intel",
    "00:24:d7": "Intel",
    "3c:6a:9d": "Intel",
}

def lookup_vendor(mac: str) -> str:
    """Look up vendor name from MAC address."""
    clean_mac = mac.lower().replace("-", ":").strip()
    prefix = clean_mac[:8]
    if prefix in OUI_PREFIXES:
        return OUI_PREFIXES[prefix]
    
    # Check 2nd bit of first octet for randomized/private MAC address
    try:
        first_byte = int(clean_mac.split(":")[0], 16)
        if first_byte & 0x02:
            return "Private / Randomized MAC (iOS/Android/Windows)"
    except Exception:
        pass

    return "Generic Network Device"


def guess_device_type(hostname: str, vendor: str) -> str:
    """Guess device icon type based on hostname and vendor."""
    h = hostname.lower()
    v = vendor.lower()
    
    if "iphone" in h or "galaxy" in h or "pixel" in h or "android" in h:
        return "smartphone"
    if "macbook" in h or "laptop" in h or "thinkpad" in h:
        return "laptop"
    if "mac" in h or "pc" in h or "desktop" in h or "windows" in h:
        return "desktop"
    if "tv" in h or "roku" in h or "chromecast" in h or "firetv" in h or "shield" in h:
        return "tv"
    if "playstation" in v or "xbox" in v or "nintendo" in v or "ps4" in h or "ps5" in h:
        return "gamepad"
    if "cam" in h or "ring" in v or "doorbell" in h or "floodlight" in h:
        return "camera"
    if "unifi" in h or "router" in h or "gateway" in h or "switch" in h or "ap" in h:
        return "router"
    if "trmnl" in h or "espressif" in v or "hue" in v or "bulb" in h:
        return "iot"
    if "apple" in v:
        return "smartphone"
    return "device"
