from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, List


class RewardActionType(str, Enum):
    KEYPRESS = 'keypress'


@dataclass
class RewardAction:
    type: RewardActionType
    value: str

    @staticmethod
    def from_dict(as_dict: dict) -> 'RewardAction':
        return RewardAction(
            type=RewardActionType(as_dict.get('type')),
            value=as_dict.get('value')
        )


@dataclass
class RewardConfig:
    id: Optional[str]
    title: str
    cost: int
    actions: Dict[str, RewardAction]

    @staticmethod
    def from_dict(as_dict: dict) -> 'RewardConfig':
        return RewardConfig(
            id=as_dict.get('id'),
            title=as_dict.get('title'),
            cost=as_dict.get('cost'),
            actions={
                key: RewardAction.from_dict(value) for (key, value) in as_dict.get('actions', dict()).items()
            }
        )


@dataclass
class ClientConfig:
    auto_fulfill: bool
    refund: bool
    rewards: List[RewardConfig]

    @staticmethod
    def from_dict(as_dict: dict) -> 'ClientConfig':
        return ClientConfig(
            auto_fulfill=as_dict.get('autoFulfill', False),
            refund=as_dict.get('refund', False),
            rewards=[
                RewardConfig.from_dict(r) for r in as_dict.get('rewards', list())
            ]
        )
