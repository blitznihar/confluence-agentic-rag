import base64
import requests
from typing import Any, Dict, List


class ConfluenceClient:
    def __init__(self, base_url: str, email: str, api_token: str):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()

        auth_str = f"{email}:{api_token}".encode("utf-8")
        encoded_auth = base64.b64encode(auth_str).decode("utf-8")
        self.session.headers.update(
            {
                "Authorization": f"Basic {encoded_auth}",
                "Accept": "application/json",
            }
        )

    def search_pages(self, cql: str, limit: int = 10) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/wiki/rest/api/content/search"
        r = self.session.get(url, params={"cql": cql, "limit": limit}, timeout=30)
        r.raise_for_status()
        return r.json().get("results", [])

    def get_page(self, page_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/wiki/rest/api/content/{page_id}"
        params = {"expand": "body.storage,version,space,_links"}
        r = self.session.get(url, params=params, timeout=30)
        r.raise_for_status()
        return r.json()

    def page_url(self, page_obj: dict) -> str:
        links = page_obj.get("_links", {}) or {}
        webui = links.get("webui", "")

        if not webui:
            return self.base_url

        # ✅ If Confluence ever returns an absolute URL, don't prepend base_url
        if webui.startswith("http://") or webui.startswith("https://"):
            return webui

        base_path = links.get("base", "/wiki")  # usually "/wiki"
        if not base_path.startswith("/"):
            base_path = "/" + base_path
        if not webui.startswith("/"):
            webui = "/" + webui

        return f"{self.base_url}{base_path}{webui}"
