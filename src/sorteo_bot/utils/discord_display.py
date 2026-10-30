from typing import Protocol


class DisplayableMember(Protocol):
    @property
    def display_name(self) -> str: ...
    @property
    def nick(self) -> str | None: ...
    @property
    def name(self) -> str: ...


def display_name_of(member: DisplayableMember) -> str:
    # en discord manda el nick, luego el display_name y por último el nombre base
    if member.nick:
        return member.nick
    if member.display_name:
        return member.display_name
    return member.name
