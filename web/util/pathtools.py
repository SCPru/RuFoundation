from pathlib import Path


class UnsafePathError(ValueError):
    pass


def media_safe_path(media_root: str | Path, path: str | Path, *, must_exist: bool = False) -> Path:
    relative = Path(path)
    media_root = Path(media_root)

    if relative.anchor:
        raise UnsafePathError('Anchor paths restricled.')

    candidate = (media_root / relative).resolve(strict=must_exist)

    try:
        candidate.relative_to(media_root)
    except ValueError as exc:
        raise UnsafePathError('Path extends beyond the media directory.') from exc

    return candidate