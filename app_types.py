from dataclasses import dataclass, field
from typing import List

@dataclass
class ItemAddress:
    category: str
    item_name: str

@dataclass
class ItemsToCompute:
    data_version: int = -1
    addr_list: List[ItemAddress] = field(default_factory=list)

@dataclass
class ItemsComputed:
    addr_list: List[ItemAddress] = field(default_factory=list)

@dataclass
class PresentationConfig:
    text_color: str = "black"
    addr_list: List[ItemAddress] = field(default_factory=list)

@dataclass
class ResultPollingState:
    compute_timestamp: int
    missing_addr_list: List[ItemAddress] = field(default_factory=list)

