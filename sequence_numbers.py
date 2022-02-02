from pathlib import Path

import diskcache


class SequenceNumbers:
    def __init__(self, root_cache_dir:str) -> None:
        self._cache = diskcache.Cache(Path(root_cache_dir)/"sequence_numbers")
        self._cache.clear()
        
    def generate(self, key:str) -> int:
        return self._cache.incr(key, delta=1, default=1)
