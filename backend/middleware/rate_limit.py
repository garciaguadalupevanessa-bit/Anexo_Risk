"""Rate limiting middleware for Anexo Risk.

Provides simple in-memory rate limiting per IP address.
"""
from __future__ import annotations

import os
import time
from collections import defaultdict
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiter."""

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        # Allow higher limit in test environments
        env = os.getenv("TESTING", "").lower()
        self.rpm = requests_per_minute if env != "true" else 99999
        self.hits: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        # Clean old entries
        self.hits[client_ip] = [
            t for t in self.hits[client_ip] if now - t < 60
        ]

        if len(self.hits[client_ip]) >= self.rpm:
            return Response(
                content='{"error": "Rate limit exceeded"}',
                status_code=429,
                media_type="application/json",
            )

        self.hits[client_ip].append(now)
        return await call_next(request)
