from __future__ import annotations

import threading
import time
import urllib.error
import urllib.request

import uvicorn

from dota2_coach.config import Settings


class DesktopBridge:
    def close(self) -> None:
        import webview

        for window in webview.windows:
            window.destroy()

    def minimize(self) -> None:
        import webview

        if webview.windows:
            webview.windows[0].minimize()

    def set_on_top(self, enabled: bool) -> bool:
        import webview

        if webview.windows:
            webview.windows[0].on_top = bool(enabled)
        return bool(enabled)


def wait_for_server(url: str, timeout: float = 20.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(url, timeout=1)
            return
        except (OSError, urllib.error.URLError):
            time.sleep(0.1)
    raise RuntimeError(f"Desktop server did not start at {url}")


def launch_desktop(
    settings: Settings,
    host: str | None = None,
    port: int | None = None,
) -> int:
    try:
        import webview
    except ImportError:
        print("pywebview is required for the desktop overlay. Run: uv sync")
        return 1

    bind_host = host or "127.0.0.1"
    bind_port = port or settings.port
    server = uvicorn.Server(
        uvicorn.Config(
            "dota2_coach.api.app:create_app",
            factory=True,
            host=bind_host,
            port=bind_port,
            log_level="warning",
        )
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{bind_port}/"
    wait_for_server(url)
    webview.create_window(
        "Dota 2 Coach",
        url,
        width=1180,
        height=760,
        min_size=(920, 620),
        frameless=True,
        easy_drag=False,
        on_top=False,
        background_color="#07090c",
        js_api=DesktopBridge(),
    )
    webview.start()
    server.should_exit = True
    return 0
