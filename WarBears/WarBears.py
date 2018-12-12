from iconservice import *

from .CryptoBears.CryptoBears import CryptoBear


class WarBear(CryptoBear):

    @external(readonly=True)
    def hello(self) -> str:
        return 'hello'
