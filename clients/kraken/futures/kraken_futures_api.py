import time
import hashlib
import hmac
import base64
import json
import urllib.request as urllib2
import ssl


class KrakenFuturesAPIClient:
    def __init__(self, api_keys, timeout=10, checkCertificate=True):
        self.api_keys = api_keys
        self.apiPath = "https://futures.kraken.com/derivatives"
        self.timeout = timeout
        self.nonce = 0
        self.checkCertificate = checkCertificate
        
    # returns all instruments with specifications
    def get_instruments(self):
        endpoint = "/api/v3/instruments"
        return self.make_request("GET", endpoint)

    # returns market data for all instruments
    def get_tickers(self):
        endpoint = "/api/v3/tickers"
        return self.make_request("GET", endpoint)

    # returns the entire order book of a futures
    def get_orderbook(self, symbol):
        endpoint = "/api/v3/orderbook"
        postUrl = "symbol=%s" % symbol
        return self.make_request("GET", endpoint, postUrl=postUrl)

    # returns historical data for futures and indices
    def get_history(self, symbol, lastTime=""):
        endpoint = "/api/v3/history"
        if lastTime != "":
            postUrl = "symbol=%s&lastTime=%s" % (symbol, lastTime)
        else:
            postUrl = "symbol=%s" % symbol
        return self.make_request("GET", endpoint, postUrl=postUrl)

    ##### private endpoints #####

    # returns key account information
    # Deprecated because it returns info about the Futures margin account
    # Use get_accounts instead
    def get_account(self):
        endpoint = "/api/v3/account"
        return self.make_request("GET", endpoint)

    # returns key account information
    def get_accounts(self):
        endpoint = "/api/v3/accounts"
        return self.make_request("GET", endpoint)

    # places an order
    def send_order(self, orderType, symbol, side, size, limitPrice=None, stopPrice=None, clientOrderId=None):
        endpoint = "/api/v3/sendorder"
        postBody = "orderType=%s&symbol=%s&side=%s&size=%s" % (orderType, symbol, side, size)

        if orderType == 'lmt' and limitPrice is not None:
            postBody += "&limitPrice=%s" % limitPrice

        if orderType == "stp" and stopPrice is not None:
            postBody += "&stopPrice=%s" % stopPrice

        if clientOrderId is not None:
            postBody += "&cliOrdId=%s" % clientOrderId

        return self.make_request("POST", endpoint, postBody=postBody)

    def modify_order(self, order_id, lmt_price=None, new_size=None):
        endpoint = "/api/v3/editorder"

        postBody = "orderId=%s" % (order_id)
        if lmt_price is not None:
            postBody += "&limitPrice=%s" % lmt_price
        if new_size is not None:
            postBody += "&size=%s" % new_size

        return self.make_request("POST", endpoint, postBody=postBody)

    # cancels an order
    def cancel_order(self, order_id=None, cli_ord_id=None):
        endpoint = "/api/v3/cancelorder"

        if order_id is None:
            postBody = "cliOrdId=%s" % cli_ord_id
        else:
            postBody = "order_id=%s" % order_id

        return self.make_request("POST", endpoint, postBody=postBody)

    # cancel all orders
    def cancel_all_orders(self, symbol=None):
        endpoint = "/api/v3/cancelallorders"
        if symbol is not None:
            postbody = "symbol=%s" % symbol
        else:
            postbody = ""

        return self.make_request("POST", endpoint, postBody=postbody)


    # cancel all orders after
    def cancel_all_orders_after(self, timeoutInSeconds=60):
        endpoint = "/api/v3/cancelallordersafter"
        postbody = "timeout=%s" % timeoutInSeconds

        return self.make_request("POST", endpoint, postBody=postbody)

    # places or cancels orders in batch
    def send_batchorder(self, jsonElement):
        endpoint = "/api/v3/batchorder"
        postBody = "json=%s" % jsonElement
        return self.make_request("POST", endpoint, postBody=postBody)

    # returns all open orders
    def get_openorders(self):
        endpoint = "/api/v3/openorders"
        return self.make_request("GET", endpoint)

    # returns filled orders
    def get_fills(self, lastFillTime=""):
        endpoint = "/api/v3/fills"
        if lastFillTime != "":
            postUrl = "lastFillTime=%s" % lastFillTime
        else:
            postUrl = ""
        return self.make_request("GET", endpoint, postUrl=postUrl)

    # returns all open positions
    def get_openpositions(self):
        endpoint = "/api/v3/openpositions"
        return self.make_request("GET", endpoint)

    def get_recentorders(self, symbol=""):
        endpoint = "/api/v3/recentorders"
        if symbol != "":
            postUrl = "symbol=%s" % symbol
        else:
            postUrl = ""
        return self.make_request("GET", endpoint, postUrl=postUrl)

    # sends an xbt withdrawal request
    def send_withdrawal(self, targetAddress, currency, amount):
        endpoint = "/api/v3/withdrawal"
        postBody = "targetAddress=%s&currency=%s&amount=%s" % (targetAddress, currency, amount)
        return self.make_request("POST", endpoint, postBody=postBody)

    # returns xbt transfers
    def get_transfers(self, lastTransferTime=""):
        endpoint = "/api/v3/transfers"
        if lastTransferTime != "":
            postUrl = "lastTransferTime=%s" % lastTransferTime
        else:
            postUrl = ""
        return self.make_request("GET", endpoint, postUrl=postUrl)

    # returns all notifications
    def get_notifications(self):
        endpoint = "/api/v3/notifications"
        return self.make_request("GET", endpoint)

    # makes an internal transfer
    def transfer(self, fromAccount, toAccount, unit, amount):
        endpoint = "/api/v3/transfer"
        postBody = "fromAccount=%s&toAccount=%s&unit=%s&amount=%s" % (fromAccount, toAccount, unit, amount)
        return self.make_request("POST", endpoint, postBody=postBody)

    # signs a message
    def sign_message(self, endpoint, nonce, postData):
        # step 1: concatenate postData, nonce + endpoint                
        message = postData + nonce + endpoint

        # step 2: hash the result of step 1 with SHA256
        sha256_hash = hashlib.sha256()
        sha256_hash.update(message.encode('utf8'))
        hash_digest = sha256_hash.digest()

        # step 3: base64 decode apiPrivateKey
        secretDecoded = base64.b64decode(self.api_keys["secret"])

        # step 4: use result of step 3 to has the result of step 2 with HMAC-SHA512
        hmac_digest = hmac.new(secretDecoded, hash_digest, hashlib.sha512).digest()

        # step 5: base64 encode the result of step 4 and return
        return base64.b64encode(hmac_digest)

    # creates a unique nonce
    def get_nonce(self):
        self.nonce = (self.nonce + 1) & 8191
        return str(int(time.time() * 1000)) + str(self.nonce).zfill(4)

    # sends an HTTP request
    def make_request(self, requestType, endpoint, postUrl="", postBody=""):
        # create authentication headers
        nonce = self.get_nonce()
        postData = postUrl + postBody
        signature = self.sign_message(endpoint, nonce, postData)
        authentHeaders = {"APIKey": self.api_keys["key"], "Nonce": nonce, "Authent": signature}

        # create request
        url = self.apiPath + endpoint + "?" + postUrl
        request = urllib2.Request(url, str.encode(postBody), authentHeaders)
        request.get_method = lambda: requestType

        # read response
        if self.checkCertificate:
            response = urllib2.urlopen(request, timeout=self.timeout)
        else:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            response = urllib2.urlopen(request, context=ctx, timeout=self.timeout)

        response = response.read().decode("utf-8")

        # return
        return json.loads(response)
