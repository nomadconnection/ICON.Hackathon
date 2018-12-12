import os

from iconsdk.builder.call_builder import CallBuilder
from iconsdk.builder.transaction_builder import DeployTransactionBuilder, CallTransactionBuilder
from iconsdk.libs.in_memory_zip import gen_deploy_data_content
from iconsdk.signed_transaction import SignedTransaction
from iconservice.base.address import Address
from tbears.libs.icon_integrate_test import IconIntegrateTestBase, SCORE_INSTALL_ADDRESS

DIR_PATH = os.path.abspath(os.path.dirname(__file__))


class TestCryptoBears(IconIntegrateTestBase):
    TEST_HTTP_ENDPOINT_URI_V3 = "http://127.0.0.1:9000/api/v3"
    SCORE_PROJECT = os.path.abspath(os.path.join(DIR_PATH, '..'))
    BEAR_FACTORY = os.path.abspath(os.path.join(DIR_PATH, '../../../BearFactory'))

    def setUp(self):
        super().setUp()
        self.icon_service = None
        self._score_address = self._deploy_score(score_path=self.SCORE_PROJECT)['scoreAddress']
        self._bear_factory = \
            self._deploy_score(score_path=self.BEAR_FACTORY, params={"_score": self._score_address})['scoreAddress']

    def _deploy_score(self, score_path: str, to: str = SCORE_INSTALL_ADDRESS, params: dict = None) -> dict:
        transaction = DeployTransactionBuilder() \
            .from_(self._test1.get_address()) \
            .to(to) \
            .step_limit(100_000_000_000) \
            .nid(3) \
            .nonce(100) \
            .content_type("application/zip") \
            .content(gen_deploy_data_content(score_path)) \
            .params(params) \
            .build()

        signed_transaction = SignedTransaction(transaction, self._test1)
        tx_result = self.process_transaction(signed_transaction, self.icon_service)

        self.assertTrue('status' in tx_result)
        self.assertEqual(1, tx_result['status'])
        self.assertTrue('scoreAddress' in tx_result)

        return tx_result

    def test_score_update(self):
        tx_result = self._deploy_score(score_path=self.SCORE_PROJECT, to=self._score_address)

        self.assertEqual(self._score_address, tx_result['scoreAddress'])

    def test_call_name(self):
        call = self._icx_call(_method="name")
        self._name = self.process_call(call, self.icon_service)
        print("Name : " + self._name)

        self.assertEqual("CryptoBears", self._name)

    def test_call_symbol(self):
        call = self._icx_call(_method="symbol")
        self._symbol = self.process_call(call, self.icon_service)
        print("Symbol : " + self._symbol)

        self.assertEqual("CBT", self._symbol)

    def test_call_balance_of(self):
        call = self._icx_call(_method="balanceOf", _params={"_owner": self._test1.get_address()})
        self._balanceBefore = self.process_call(call, self.icon_service)
        print("balanceBefore : " + str(self._balanceBefore))

        self.assertEqual("0x0", self._balanceBefore)

    def test_call_balance_of_after_create_crypto_bear(self):
        transaction = self._icx_sendTransaction(_to=self._bear_factory, _value=1000000000000000000,
                                                _method="createCryptoBear")
        signed_transaction = SignedTransaction(transaction, self._test1)
        tx_result = self.process_transaction(signed_transaction, self.icon_service)

        call = self._icx_call(_method="balanceOf", _params={"_owner": self._test1.get_address()})
        self._balanceAfter = self.process_call(call, self.icon_service)
        print("balanceAfter : " + str(self._balanceAfter))

        self.assertEqual("0x1", self._balanceAfter)

    def test_create_crypto_bear_called_by_ca(self):
        transaction = self._icx_sendTransaction(_to=self._bear_factory, _value=1000000000000000000,
                                                _method="createCryptoBear")
        signed_transaction = SignedTransaction(transaction, self._test1)
        tx_result = self.process_transaction(signed_transaction, self.icon_service)

        self.assertTrue('status' in tx_result)
        self.assertEqual(1, tx_result['status'])

    def test_create_crypto_bear_called_by_eoa(self):
        print("------ Expecting error msg here ------")
        transaction = self._icx_sendTransaction(_to=self._score_address, _method="createCryptoBear",
                                                _params={"_bearDNA": b'12345', "_address": self._test1.get_address()})
        signed_transaction = SignedTransaction(transaction, self._test1)
        tx_result = self.process_transaction(signed_transaction, self.icon_service)

        self.assertTrue('status' in tx_result)
        self.assertEqual(0, tx_result['status'])
        print("  --------------------------------------")

    def test_call_get_token_id_after_create_crypto_bear(self):
        transaction = self._icx_sendTransaction(_to=self._bear_factory, _value=1000000000000000000,
                                                _method="createCryptoBear")
        signed_transaction = SignedTransaction(transaction, self._test1)
        tx_result = self.process_transaction(signed_transaction, self.icon_service)
        call = self._icx_call(_method="getTokenId", _params={"_address": self._test1.get_address(), "index": "0"})

        self._tokenId = self.process_call(call, self.icon_service)
        print("tokenId : " + str(self._tokenId))

        self.assertEqual(66, len(self._tokenId))
        self.assertEqual(str, type(self._tokenId))

    def test_happy_meal_after_create_crypto_bear(self):
        prerequisite = self._icx_sendTransaction(_to=self._bear_factory, _value=1000000000000000000,
                                                 _method="createCryptoBear")
        signed_prerequisite = SignedTransaction(prerequisite, self._test1)
        self.process_transaction(signed_prerequisite, self.icon_service)

        happymeal_transaction = self._icx_sendTransaction(_to=self._score_address, _value=1000000000000000000,
                                                          _method="happyMeal", _params={"_index": '0'})
        signed_transaction = SignedTransaction(happymeal_transaction, self._test1)
        tx_result = self.process_transaction(signed_transaction, self.icon_service)

        self.assertTrue('status' in tx_result)
        self.assertEqual(1, tx_result['status'])

        call_tokenid = self._icx_call(_method="getTokenId",
                                      _params={"_address": self._test1.get_address(), "index": "0"})
        self._tokenId = self.process_call(call_tokenid, self.icon_service)

        call_get_bear_level = self._icx_call(_method="getBearLevel", _params={"_tokenId": self._tokenId})
        self._bearLevel = self.process_call(call_get_bear_level, self.icon_service)
        print("BearLevelAfterHappyMeal : " + self._bearLevel)
        self.assertEqual('0x1', self._bearLevel)

    def test_call_get_bear_level(self) -> str:
        transaction = self._icx_sendTransaction(_to=self._bear_factory, _value=1000000000000000000,
                                                _method="createCryptoBear")
        signed_transaction = SignedTransaction(transaction, self._test1)
        tx_result = self.process_transaction(signed_transaction, self.icon_service)

        call_tokenid = self._icx_call(_method="getTokenId",
                                      _params={"_address": self._test1.get_address(), "index": "0"})
        self._tokenId = self.process_call(call_tokenid, self.icon_service)

        call = self._icx_call(_method="getBearLevel", _params={"_tokenId": self._tokenId})

        self._bearLevel = self.process_call(call, self.icon_service)
        print("BearLevel : " + self._bearLevel)
        self.assertEqual('0x0', self._bearLevel)

        return self._bearLevel

    def _icx_call(self, _method: str = "", _params: dict = None):
        call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self._score_address) \
            .method(_method) \
            .params(_params) \
            .build()
        return call

    def _icx_sendTransaction(self, _to: Address, _value: int = 0, _method: str = "", _params: dict = None):
        transaction = CallTransactionBuilder() \
            .from_(self._test1.get_address()) \
            .to(_to) \
            .step_limit(100_000_000_000) \
            .value(_value) \
            .nid(3) \
            .method(_method) \
            .params(_params) \
            .build()
        return transaction
