class Symbol:
    def __init__(self, string: str):
        pieces: list[str] = string.split("-")

        self.string = string
        self.product_code = pieces[0]
        self.month_code = pieces[1]
        self.year = pieces[2]

    @property
    def firstrate_string(self) -> str:
        return f"{self.product_code}_{self.month_code}{self.year[-2:]}"

    def __repr__(self):
        return self.string


if __name__ == "__main__":
    sym = Symbol("6E-M-2024")
    print(sym)
