from typing import Callable, Optional
import requests
import socket
from threading import Lock


_getaddrinfo_lock: Lock = Lock()


def _with_patched_getaddrinfo[T](af: socket.AddressFamily, f: Callable[[], T]) -> T:
    with _getaddrinfo_lock:
        old_getaddrinfo = socket.getaddrinfo
        def _getaddrinfo(*args, **kwargs):  # type: ignore
            responses = old_getaddrinfo(*args, **kwargs)  # type: ignore
            return [response for response in responses if response[0] == af]
        socket.getaddrinfo = _getaddrinfo
        try:
            return f()
        finally:
            socket.getaddrinfo = old_getaddrinfo


def _get_ip() -> Optional[str]:
    resp = requests.get(f"https://domains.google.com/checkip")
    if 200 <= resp.status_code < 300:
        return resp.content.decode("utf-8")
    return None


def get_ipv4() -> Optional[str]:
    return _with_patched_getaddrinfo(socket.AF_INET, _get_ip)


def get_ipv6() -> Optional[str]:
    return _with_patched_getaddrinfo(socket.AF_INET6, _get_ip)
