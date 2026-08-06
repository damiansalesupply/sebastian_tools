from __future__ import annotations

from .base import SiteAdapter
from .eldorado import EldoradoSite
from .g2g import G2GSite
from .playerauctions import PlayerAuctionsSite

SITE_REGISTRY: dict[str, type[SiteAdapter]] = {
    EldoradoSite.name: EldoradoSite,
    G2GSite.name: G2GSite,
    PlayerAuctionsSite.name: PlayerAuctionsSite,
}


def build_adapter(name: str, config: dict | None = None) -> SiteAdapter:
    try:
        cls = SITE_REGISTRY[name]
    except KeyError:
        raise ValueError(f"Unknown site '{name}'. Known sites: {', '.join(sorted(SITE_REGISTRY))}") from None
    return cls(config)


__all__ = ["SiteAdapter", "SITE_REGISTRY", "build_adapter", "EldoradoSite", "G2GSite", "PlayerAuctionsSite"]
