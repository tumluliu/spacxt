
from dataclasses import dataclass, field
from typing import Dict, Any
import time, uuid

@dataclass
class A2AMessage:
    type: str
    sender: str
    receiver: str
    payload: Dict[str, Any]
    mid: str = field(default_factory=lambda: str(uuid.uuid4()))
    ts: float = field(default_factory=time.time)

# Types:
# - RELATION_PROPOSE {relation, basis}
# - RELATION_ACK {relation, decision: accept/reject, reason?}
# - STATE_UPDATE {node_id, fields}
