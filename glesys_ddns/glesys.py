from typing import Any
from dataclasses import dataclass, asdict
import requests


_DEFAULT_API_URL = "api.glesys.com"


class GleSYSError(Exception):
    def message(self) -> str:
        return "\n".join(self.args)


@dataclass
class Record:
    recordid: int
    host: str
    type: str
    data: str
    ttl: int

    @staticmethod
    def from_dict(_dict: dict[str, Any]) -> 'Record':
        filtered_fields = {k: v for k, v in _dict.items() if k in Record.__dataclass_fields__}
        return Record(**filtered_fields)


class GleSYS:
    _api_user: str
    _api_key: str
    _api_url: str

    def __init__(self, api_user: str, api_key: str, api_url: str = _DEFAULT_API_URL) -> None:
        self._api_user = api_user
        self._api_key = api_key
        self._api_url = api_url

    def _request_url(self, path: str) -> str:
        return f"https://{self._api_user}:{self._api_key}@{self._api_url}/{path}"

    def _post(self, path: str, json: Any) -> requests.Response:
        url = self._request_url(path)
        resp = requests.post(url, json=json, headers={"Content-Type": "application/json"})
        if not resp.ok:
            raise GleSYSError(f"GleSYS POST request to {path} failed with status code {resp.status_code}")
        return resp

    def list_records(self, domain: str) -> list[Record]:
        resp = self._post("domain/listrecords", {"domainname": domain})
        return [Record.from_dict(record) for record in resp.json()["response"]["records"]]

    def update_record(self, record: Record) -> None:
        self._post("domain/updaterecord", asdict(record))
