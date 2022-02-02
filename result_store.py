from xmlrpc.client import Boolean
import diskcache

class ResultStore:
    def __init__(self, cache_dir:str) -> None:
        self._cache = diskcache.Cache(cache_dir)

    def get_result(self, cat:str, item_name:str) -> str:
        key = self._make_key(cat, item_name)
        return self._cache.get(key)

    def set_result(self, cat:str, item_name:str, res:str) -> None:
        key = self._make_key(cat, item_name)
        return self._cache.set(key, res)

    def has_result(self, cat:str, item_name:str) -> Boolean:
        key = self._make_key(cat, item_name)
        return key in self._cache

    def clear_all_results(self) -> None:
        self._cache.clear()

    def _make_key(self, cat:str, item_name:str) -> str:
        return f"C_{cat}--I_{item_name}"
