import abc
import typing as T

from graia.application import GraiaMiraiApplication, Group, Friend, MessageChain
from graia.broadcast import Broadcast, ExecutionStop

from handler.abstract_message_handler import AbstractMessageHandler


class SenderFilterQueryHandler(AbstractMessageHandler, metaclass=abc.ABCMeta):
    def __init__(self, tag: str,
                 settings: dict,
                 bcc: Broadcast,
                 allow_friend: T.Optional[T.Sequence[int]],
                 allow_group: T.Optional[T.Sequence[int]]):
        super().__init__(tag, settings, bcc)
        self.allow_friend = allow_friend
        self.allow_group = allow_group

    def judge(self, app: GraiaMiraiApplication,
              subject: T.Union[Group, Friend],
              message: MessageChain) -> T.NoReturn:
        if isinstance(subject, Group):
            if (self.allow_group is not None) and (subject.id in self.allow_group):
                raise ExecutionStop()
        elif isinstance(subject, Friend):
            if (self.allow_friend is not None) and (subject.id in self.allow_friend):
                raise ExecutionStop()
