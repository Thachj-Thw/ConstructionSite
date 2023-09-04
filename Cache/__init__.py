from typing import Union
from collections.abc import Callable
from pathlib import Path
import pickle
import os


class Cache:
    def __init__(self, obj: object, name: str) -> None:
        cache_dir = Path.home()/("."+name)
        if not os.path.isdir(cache_dir):
            os.makedirs(cache_dir)
        self._path = os.path.join(cache_dir, name+".cache")
        if not os.path.isfile(self._path):
            with open(self._path, "wb") as f:
                pickle.dump({}, f, pickle.HIGHEST_PROTOCOL)
        self._data = {}
        self._obj = obj
        self._error = False
        if "__cache__" not in dir(obj):
            self._error = True
            print("__cache__ method not found!")
        else:
            for cache_obj in self._obj.__cache__():
                self._data[cache_obj.id] = cache_obj
    
    def load(self) -> dict:
        if self._error:
            return
        with open(self._path, "rb") as f:
            cache = pickle.load(f)
        for _id in cache.keys():
            if _id in self._data:
                self._data[_id].set(cache[_id])
        return cache
    
    def update(self) -> None:
        cache = {}
        for _id in self._data.keys():
            cache[_id] = self._data[_id].get()
        with open(self._path, "wb") as f:
            pickle.dump(cache, f, pickle.HIGHEST_PROTOCOL)



class CacheObject:
    def __init__(self, _id: str, getter: Callable, setter: Callable, default: Union[str, int, float]) -> None:
        self.id = _id
        self.getter = getter
        self.setter = setter
        self.default = default
    
    def get(self) -> Union[str, int, float]:
        return self.getter()

    def set(self, value=None) -> None:
        return self.setter(value if value is not None else self.default)
