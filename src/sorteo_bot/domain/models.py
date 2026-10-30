from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Participant:
    user_id: int
    entries: int

    def __post_init__(self) -> None:
        if self.user_id <= 0:
            raise ValueError(f"user_id inválido: {self.user_id}")
        if self.entries <= 0:
            raise ValueError(f"entries debe ser > 0 (recibido: {self.entries})")
