import dwollav2
from logzero import logger

# Navigate to https://www.dwolla.com/applications (production) or https://dashboard-sandbox.dwolla.com/applications (Sandbox) for your application key and secret.

DWOLLA_KEY='AhsM66nKvorWWIwJL9WNCE3wO0FNIg0ajsB7v4lOQlUvnNGNyY'
DWOLLA_SECRET='o5863B3xHXYA60DQo1Gnsrl9zKKoOyGdOrayJTOQWNRm2a18Pd'



class DwollaClient():
    
    __instance = None
    
    _client = None
    
    _token = None
    
    
    @property
    def token(self):
        return self._token
    
    @property
    def client(self):
        return self._client

    def refresh(self):
        self._token = self.client.Auth.client()

        
    def __init__(self):
        self._client = dwollav2.Client(key = DWOLLA_KEY,
                                        secret = DWOLLA_SECRET,
                                        environment = 'sandbox') # optional - defaults to production
        self.refresh()
        
    @staticmethod
    def instance():
        if not DwollaClient.__instance:
            DwollaClient.__instance = DwollaClient()
        return DwollaClient.__instance




def dwolla_get_url(url):
    try:
        result = DwollaClient.instance().token.get(url)
        return result.body
    except Exception as e:
        logger.error("Could not get url: %s %s " % (url, e))
    return None

def dwolla_create_user(user):

    json = user.to_json()

    try:
        customer = DwollaClient.instance().token.post('customers',json)
        url = customer.headers['location']
        user.dwolla_url = url
        user.save()
        return True
    except Exception as e:
        logger.error("could not get customer location %s " % e)

    return False

def dwolla_update_user(user):

    json = user.to_update_json()

    try:
        customer = DwollaClient.instance().token.post('customers/%s' % user.dwolla_id, json)

        if customer.status == 200:
            return True
    except Exception as e:
        logger.error("could not get customer location %s " % e)

    return False

def dwolla_generate_funding_source_token(user):

    if user.dwolla_url:
        funding_token_req = '%s/iav-token' % user.dwolla_url
        logger.debug("funding token %s " % funding_token_req)
        try:
            request = DwollaClient.instance().token.post(funding_token_req)
            return request.body['token']
        except Exception as e:
            logger.error("could not get dwolla account funding token %s " % e)

    return None



def dwolla_get_user_balance(user):

    items = dwolla_get_funding_sources(user)

    for item in items:
        if item['type'] == 'balance':
            return item

    return None

def dwolla_get_user_bank_accounts(user):

    items = dwolla_get_funding_sources(user)

    to_return = []
    if items:
        for item in items:
            logger.debug("ITEM: %s " % item['type'])
            if item['type'] == 'bank':
                to_return.append(item)

    return to_return




def dwolla_get_funding_sources(user):

    if user.dwolla_url:
        sources_url = '%s/funding-sources' % user.dwolla_url
        try:
            results = DwollaClient.instance().token.get(sources_url)

            items = []

            sources = results.body['_embedded']['funding-sources']

            for item in sources:
                if item['status'] == 'verified':

                    if item['type'] == 'balance':
                        item['balance'] = dwolla_get_balance(item)

                    items.append(item)

            return items

        except Exception as e:
            logger.error("could not get funding source %s " % e)

    return None


def dwolla_get_balance(funding_source):

    try:
        balance_url = funding_source['_links']['balance']['href']
        logger.info("balance url %s " % balance_url)
        results = DwollaClient.instance().token.get(balance_url)

        return results.body

    except Exception as e:
        logger.error("could not get balance %s " % e)

    return {'balance': {'currency': 'USD', 'value': '0.00'}}



def dwolla_create_transfer(purchase):

    request_body = {
        '_links': {
            'source': {
                'href': 'https://api-sandbox.dwolla.com/funding-sources/%s' % purchase.sender_account_id
            },
            'destination': {
                'href': purchase.receiver_account_id
            }
        },
        'amount': {
            'currency': 'USD',
            'value': "%0.2f" % (purchase.total,),
        },
        'correlationId': purchase.id,
    }

    transfer = DwollaClient.instance().token.post('transfers',request_body)



    return transfer

def dwolla_get_transfers(user):

    url = '%s/transfers' % user.dwolla_url
    try:
        transferlist = DwollaClient.instance().token.get(url)
        return transferlist.body['_embedded']['transfers']

    except Exception as e:
        logger.error("could not get transfer list: %s " % e)

    return None