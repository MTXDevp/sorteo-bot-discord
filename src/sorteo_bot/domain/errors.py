class SorteoError(Exception):
    pass


class NoParticipantsError(SorteoError):
    pass


class InvalidEntriesError(SorteoError):
    def __init__(self, value: int) -> None:
        super().__init__(f"Las participaciones deben ser > 0 (recibido: {value}).")
        self.value = value


class InsufficientEntriesError(SorteoError):
    pass
