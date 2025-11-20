"""Entry point for running AKLP as a module (python -m aklp)."""

import asyncio
import sys

from aklp.cli import app

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    app()
