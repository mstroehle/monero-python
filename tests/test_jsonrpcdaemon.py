import decimal
import os
import responses

from monero.const import NET_STAGE
from monero.daemon import Daemon
from monero.backends.jsonrpc import JSONRPCDaemon
from monero.transaction import Transaction

from .base import JSONTestCase

class JSONRPCDaemonTestCase(JSONTestCase):
    jsonrpc_url = 'http://127.0.0.1:18081/json_rpc'
    mempool_url = 'http://127.0.0.1:18081/get_transaction_pool'
    transactions_url = 'http://127.0.0.1:18081/get_transactions'
    sendrawtransaction_url = 'http://127.0.0.1:18081/sendrawtransaction'
    data_subdir = 'test_jsonrpcdaemon'

    def setUp(self):
        self.daemon = Daemon(JSONRPCDaemon())

    @responses.activate
    def test_basic_info(self):
        responses.add(responses.POST, self.jsonrpc_url,
            json=self._read('test_basic_info-get_info.json'),
            status=200)
        responses.add(responses.POST, self.jsonrpc_url,
            json=self._read('test_basic_info-get_info.json'),
            status=200)
        self.assertTrue(self.daemon.info())
        self.assertEqual(self.daemon.height(), 294993)

    @responses.activate
    def test_net(self):
        responses.add(responses.POST, self.jsonrpc_url,
            json=self._read('test_basic_info-get_info.json'),
            status=200)
        self.assertEqual(self.daemon.net, NET_STAGE)
        self.daemon.net
        self.assertEqual(len(responses.calls), 1, "net value has not been cached?")

    @responses.activate
    def test_info_then_net(self):
        responses.add(responses.POST, self.jsonrpc_url,
            json=self._read('test_basic_info-get_info.json'),
            status=200)
        self.daemon.info()
        self.assertEqual(self.daemon.net, NET_STAGE)
        self.assertEqual(len(responses.calls), 1, "net value has not been cached?")

    @responses.activate
    def test_mempool(self):
        responses.add(responses.POST, self.mempool_url,
            json=self._read('test_mempool-transactions.json'),
            status=200)
        txs = self.daemon.mempool()
        self.assertEqual(len(txs), 2)
        self.assertEqual(txs[0].confirmations, 0)
        self.assertEqual(txs[1].confirmations, 0)
        self.assertGreater(txs[0].fee, 0)
        self.assertGreater(txs[1].fee, 0)

    @responses.activate
    def test_block(self):
        responses.add(responses.POST, self.jsonrpc_url,
            json=self._read("test_block-423cd4d170c53729cf25b4243ea576d1e901d86e26c06d6a7f79815f3fcb9a89.json"),
            status=200)
        responses.add(responses.POST, self.transactions_url,
            json=self._read("test_block-423cd4d170c53729cf25b4243ea576d1e901d86e26c06d6a7f79815f3fcb9a89-txns.json"),
            status=200)
        blk = self.daemon.block("423cd4d170c53729cf25b4243ea576d1e901d86e26c06d6a7f79815f3fcb9a89")
        self.assertEqual(
            blk.hash,
            "423cd4d170c53729cf25b4243ea576d1e901d86e26c06d6a7f79815f3fcb9a89")
        self.assertEqual(blk.height, 451992)
        self.assertIsInstance(blk.reward, decimal.Decimal)

        self.assertIn("24fb42f9f324082658524b29b4cf946a9f5fcfa82194070e2f17c1875e15d5d0", blk)
        for tx in blk.transactions:
            self.assertIn(tx, blk)

        # tx not in block
        self.assertNotIn("e3a3b8361777c8f4f1fd423b86655b5c775de0230b44aa5b82f506135a96c53a", blk)
        # wrong arg type
        self.assertRaises(ValueError, lambda txid: txid in blk, 1245)

    @responses.activate
    def test_transactions(self):
        responses.add(responses.POST, self.transactions_url,
            json=self._read('test_transactions.json'),
            status=200)
        txs = self.daemon.transactions([
            "050679bd5717cd4c3d0ed1db7dac4aa7e8a222ffc7661b249e5a595a3af37d3c",     # @471570
            "e3a3b8361777c8f4f1fd423b86655b5c775de0230b44aa5b82f506135a96c53a",     # @451993
            "e2871c4203e29433257219bc20fa58c68dc12efed8f05a86d59921969a2b97cc",     # @472279
            "035a1cfadd2f80124998f5af8c7bb6703743a4f322d0a20b7f7b502956ada59d",     # mempool
            "feed00000000000face00000000000bad00000000000beef00000000000acab0",     # doesn't exist
        ])
        self.assertEqual(len(txs), 4)
        self.assertEqual(txs[0].hash,
                "050679bd5717cd4c3d0ed1db7dac4aa7e8a222ffc7661b249e5a595a3af37d3c")
        self.assertEqual(txs[0].height, 471570)
        self.assertEqual(txs[0].size, 2826)
        self.assertEqual(txs[0].fee, decimal.Decimal('0.000331130000'))
        self.assertEqual(txs[1].hash,
                "e3a3b8361777c8f4f1fd423b86655b5c775de0230b44aa5b82f506135a96c53a")
        self.assertEqual(txs[1].height, 451993)
        self.assertEqual(txs[1].size, 2596)
        self.assertEqual(txs[1].fee, decimal.Decimal('0.000265330000'))
        self.assertEqual(txs[2].hash,
                "e2871c4203e29433257219bc20fa58c68dc12efed8f05a86d59921969a2b97cc")
        self.assertEqual(txs[2].height, 472279)
        self.assertEqual(txs[2].size, 2796)
        self.assertEqual(txs[2].fee, decimal.Decimal('0.000327730000'))
        self.assertEqual(txs[3].hash,
                "035a1cfadd2f80124998f5af8c7bb6703743a4f322d0a20b7f7b502956ada59d")
        self.assertIsNone(txs[3].height)
        self.assertEqual(txs[3].size, 2724)
        self.assertEqual(txs[3].fee, decimal.Decimal('0.000320650000'))

    @responses.activate
    def test_send_transaction(self):
        path = os.path.join(
            os.path.dirname(__file__),
            "data",
            self.data_subdir,
            "0e8fa9202e0773333360e5b9e8fb8e94272c16a8a58b6fe7cf3b4327158e3a44.tx")
        responses.add(responses.POST, self.sendrawtransaction_url,
            json=self._read('test_send_transaction.json'),
            status=200)
        tx = Transaction(
            blob=open(path, "rb").read())
        rsp = self.daemon.send_transaction(tx)
        self.assertEqual(rsp["status"], "OK")
