from pathlib import Path


class CoolPath:
    """
    Merkt sich das `cwd`, um `__str__` so zu implementieren, dass nur der Teil-Pfad von Interesse ausgegeben wird.
    """
    # NOTE: This class is not a subclass of Path because it creates problems with its internal use of __str__.

    def __init__(self, path, *, cwd=None):
        self.full_path = Path(path)
        self._cwd = Path(cwd) if cwd else None

    def __str__(self):
        if self._cwd:
            return str(self.full_path.relative_to(self._cwd))
        return str(self.full_path)

    # Delegate attribute access to the underlying Path object
    def __getattr__(self, name):
        return getattr(self.full_path, name)

    def __fspath__(self):
        return self.full_path.__fspath__()

    def __repr__(self):
        return f"CoolPath({str(self)})"

    # Delegate comparison operators
    def _compare(self, other, method):
        if isinstance(other, (CoolPath, Path)):
            other_path = other.full_path if isinstance(other, CoolPath) else other
            return method(self.full_path, other_path)
        return NotImplemented

    def __eq__(self, other):
        return self._compare(other, lambda self_path, other_path: self_path == other_path)

    def __lt__(self, other):
        return self._compare(other, lambda self_path, other_path: self_path < other_path)

    def __le__(self, other):
        return self._compare(other, lambda self_path, other_path: self_path <= other_path)

    def __gt__(self, other):
        return self._compare(other, lambda self_path, other_path: self_path > other_path)

    def __ge__(self, other):
        return self._compare(other, lambda self_path, other_path: self_path >= other_path)

    def __hash__(self):
        return hash(self.full_path)
