import os

from iconsdk.builder.call_builder import CallBuilder
from iconsdk.builder.transaction_builder import DeployTransactionBuilder, CallTransactionBuilder
from iconsdk.libs.in_memory_zip import gen_deploy_data_content
from iconsdk.signed_transaction import SignedTransaction
from tbears.libs.icon_integrate_test import IconIntegrateTestBase, SCORE_INSTALL_ADDRESS

DIR_PATH = os.path.abspath(os.path.dirname(__file__))


class TestCryptoBears(IconIntegrateTestBase):
    TEST_HTTP_ENDPOINT_URI_V3 = "http://127.0.0.1:9000/api/v3"
    SCORE_PROJECT = os.path.abspath(os.path.join(DIR_PATH, '..'))
    BEAR_FACTORY = os.path.abspath(os.path.join(DIR_PATH, '../../../BearFactory'))

    def setUp(self):
        super().setUp()

        self.icon_service = None
        # if you want to send request to network, uncomment next line and set self.TEST_HTTP_ENDPOINT_URI_V3
        # self.icon_service = IconService(HTTPProvider(self.TEST_HTTP_ENDPOINT_URI_V3))

        # install SCORE
        self._score_address = self._deploy_score(score_path=self.SCORE_PROJECT)['scoreAddress']
        self._bear_factory = \
            self._deploy_score(score_path=self.BEAR_FACTORY, params={"_score": self._score_address})['scoreAddress']

    def _deploy_score(self, score_path: str, to: str = SCORE_INSTALL_ADDRESS, params: dict = None) -> dict:
        # Generates an instance of transaction for deploying SCORE.
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

        # Returns the signed transaction object having a signature
        signed_transaction = SignedTransaction(transaction, self._test1)

        # process the transaction in local
        tx_result = self.process_transaction(signed_transaction, self.icon_service)

        self.assertTrue('status' in tx_result)
        self.assertEqual(1, tx_result['status'])
        self.assertTrue('scoreAddress' in tx_result)

        return tx_result

    def test_score_update(self):
        # update SCORE
        tx_result = self._deploy_score(score_path=self.SCORE_PROJECT, to=self._score_address)

        self.assertEqual(self._score_address, tx_result['scoreAddress'])

    def test_call_name(self):
        # Generates a call instance using the CallBuilder
        call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self._score_address) \
            .method("name") \
            .build()

        # Sends the call request
        response = self.process_call(call, self.icon_service)

        self.assertEqual("CryptoBears", response)

    def test_call_symbol(self):
        call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self._score_address) \
            .method("symbol") \
            .build()

        response = self.process_call(call, self.icon_service)

        self.assertEqual("CBT", response)

    def test_call_balance_of(self):
        call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self._score_address) \
            .method("balanceOf") \
            .params({"_owner": self._test1.get_address()}) \
            .build()

        response = self.process_call(call, self.icon_service)
        self.assertEqual("0x0", response)

    def test_call_balance_of_after_create_crypto_bear(self):
        transaction = CallTransactionBuilder() \
            .from_(self._test1.get_address()) \
            .to(self._bear_factory) \
            .step_limit(100_000_000_000) \
            .value(1000000000000000000) \
            .nid(3) \
            .method("createCryptoBear") \
            .build()

        signed_transaction = SignedTransaction(transaction, self._test1)

        tx_result = self.process_transaction(signed_transaction, self.icon_service)
        self.assertTrue('status' in tx_result)
        self.assertEqual(1, tx_result['status'])

        call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self._score_address) \
            .method("balanceOf") \
            .params({"_owner": self._test1.get_address()}) \
            .build()

        response = self.process_call(call, self.icon_service)
        self.assertEqual("0x1", response)

    def test_create_crypto_bear_called_by_ca(self) -> dict:
        transaction = CallTransactionBuilder() \
            .from_(self._test1.get_address()) \
            .to(self._bear_factory) \
            .step_limit(100_000_000_000) \
            .value(1000000000000000000) \
            .nid(3) \
            .method("createCryptoBear") \
            .build()

        signed_transaction = SignedTransaction(transaction, self._test1)

        tx_result = self.process_transaction(signed_transaction, self.icon_service)
        self.assertTrue('status' in tx_result)
        self.assertEqual(1, tx_result['status'])
        return tx_result

    def test_create_crypto_bear_called_by_eoa(self) -> dict:
        transaction = CallTransactionBuilder() \
            .from_(self._test1.get_address()) \
            .to(self._score_address) \
            .step_limit(100_000_000_000) \
            .nid(3) \
            .method("createCryptoBear") \
            .params({"_bearDNA": b'12345', "_address": self._test1.get_address()}) \
            .build()

        signed_transaction = SignedTransaction(transaction, self._test1)

        tx_result = self.process_transaction(signed_transaction, self.icon_service)
        self.assertTrue('status' in tx_result)
        self.assertEqual(0, tx_result['status'])

        return tx_result

    def test_call_get_token_id(self):
        self.test_create_crypto_bear_called_by_ca()

        call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self._score_address) \
            .method("getTokenId") \
            .params({"_address": self._test1.get_address(), "index": "0"}) \
            .build()
        response = self.process_call(call, self.icon_service)
        self._tokenId = str(response)
        self.assertEqual(66, len(response))
        self.assertEqual(str, type(response))

    def test_happy_meal(self):
        self.test_create_crypto_bear_called_by_ca()

        transaction = CallTransactionBuilder() \
            .from_(self._test1.get_address()) \
            .to(self._score_address) \
            .step_limit(100_000_000_000) \
            .nid(3) \
            .value(100000000000000000) \
            .method("happyMeal") \
            .params({"_index": '0'}) \
            .build()

        signed_transaction = SignedTransaction(transaction, self._test1)
        tx_result = self.process_transaction(signed_transaction, self.icon_service)

        self.assertTrue('status' in tx_result)
        self.assertEqual(1, tx_result['status'])

    def test_bear_level(self):
        self.test_call_get_token_id()

        call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self._score_address) \
            .method("getBearLevel") \
            .params({"_tokenId": self._tokenId}) \
            .build()

        response = self.process_call(call, self.icon_service)
        print(response)
        self.assertEqual('0x0', response)
