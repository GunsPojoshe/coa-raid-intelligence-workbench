from __future__ import annotations

import hashlib
import http.cookiejar
import json
import ssl
from dataclasses import asdict, dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urljoin
from urllib.request import HTTPCookieProcessor, Request, build_opener

BASE_URL = "https://coa.ascensionlogs.gg"
CHARACTER = "Gunspojoshe"
REALM = "Vol'Jin"
TIMEOUT = 20.0
MAX