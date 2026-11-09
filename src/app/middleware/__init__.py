"""Middleware-Module fuer G.R.E.A.T. Backend."""
from .docs_auth import DocsAuthMiddleware

__all__ = ["DocsAuthMiddleware"]