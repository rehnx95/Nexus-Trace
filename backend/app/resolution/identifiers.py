from dataclasses import dataclass


@dataclass(frozen=True)
class IdentifierEvidence:
    phone: set[str] | None = None
    account: set[str] | None = None
    plate: set[str] | None = None

    def has_shared_identifier(self, other: "IdentifierEvidence") -> bool:
        for kind in ("phone", "account", "plate"):
            left = getattr(self, kind)
            right = getattr(other, kind)
            if left and right and not left.isdisjoint(right):
                return True
        return False

    def has_conflict(self, other: "IdentifierEvidence") -> bool:
        for kind in ("phone", "account", "plate"):
            left = getattr(self, kind)
            right = getattr(other, kind)
            if left and right and left.isdisjoint(right):
                return True
        return False
