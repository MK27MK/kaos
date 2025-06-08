class Symbol:
    def __init__(self, value: str):
        pieces: list[str] = value.split("-")

        self.value = value
        self.product_code = pieces[0]
        self.month_code = pieces[1]
        self.year = pieces[2]

    @property
    def firstrate_string(self) -> str:
        return f"{self.product_code}_{self.month_code}{self.year[-2:]}"

    def __repr__(self) -> str:
        return self.value


class Venue:
    def __init__(self, name: str):
        # TODO add checks
        self.name: str = name.upper()

    def __repr__(self) -> str:
        return self.name


"CME:6E-M-2024[]"


class InstrumentId:
    def __init__(self, venue: Venue, symbol: Symbol):
        self._venue = venue
        self._symbol = symbol
        self._id = f"{venue}:{symbol}"


if __name__ == "__main__":
    sym = Symbol("6E-M-2024")
    print(sym)
