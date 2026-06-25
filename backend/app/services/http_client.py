"""HTTP helpers for external API calls."""

import ssl

import certifi


_SSL_CONTEXT: ssl.SSLContext | None = None


def ca_bundle_path() -> str:
    return certifi.where()


def ssl_context() -> ssl.SSLContext:
    global _SSL_CONTEXT
    if _SSL_CONTEXT is None:
        _SSL_CONTEXT = ssl.create_default_context(cafile=ca_bundle_path())
    return _SSL_CONTEXT
