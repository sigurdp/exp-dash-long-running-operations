from dataclasses import dataclass, field
from typing import List


@dataclass
class ItemAddress:
    category: str
    item_name: str

@dataclass
class ItemsToCompute:
    batch_id: int
    addr_list: List[ItemAddress] = field(default_factory=list)

@dataclass
class ItemsComputed:
    batch_id: int
    addr_list: List[ItemAddress] = field(default_factory=list)

@dataclass
class PresentationConfig:
    text_color: str = "black"
    addr_list: List[ItemAddress] = field(default_factory=list)
