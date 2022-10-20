from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, List

import yaml
from pydantic import BaseModel


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

    # Should be called "__dict__" but that confused the PyCharm debugger and
    # makes it impossible to inspect any instance variables
    # https://youtrack.jetbrains.com/issue/PY-43955
    def to_dict(self) -> dict:
        return {
            'type': self.type.value,
            'value': self.value
        }


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
                key: RewardAction.from_dict(action_dict)
                for (key, action_dict) in as_dict.get('actions', dict()).items()
            }
        )

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'title': self.title,
            'cost': self.cost,
            'actions': {
                key: action.to_dict() for (key, action) in self.actions.items()
            }
        }


@dataclass
class ClientConfig:
    log_level: str
    auto_fulfill: bool
    refund: bool
    rewards: List[RewardConfig]

    @staticmethod
    def from_dict(as_dict: dict) -> 'ClientConfig':
        return ClientConfig(
            log_level=as_dict.get('logLevel', 'info').upper(),
            auto_fulfill=as_dict.get('autoFulfill', False),
            refund=as_dict.get('refund', False),
            rewards=[
                RewardConfig.from_dict(r) for r in as_dict.get('rewards', list())
            ]
        )

    def to_dict(self) -> dict:
        return {
            'logLevel': self.log_level.lower(),
            'autoFulfill': self.auto_fulfill,
            'refund': self.refund,
            'rewards': [
                reward.to_dict() for reward in self.rewards
            ]
        }


class TokenFromUrlDTO(BaseModel):
    url: str


class YamlDumper(yaml.Dumper):
    """
    From: https://stackoverflow.com/a/39681672
    """
    def increase_indent(self, flow=False, indentless=False):
        return super(YamlDumper, self).increase_indent(flow, False)
