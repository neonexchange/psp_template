import dwollav2
from logzero import logger
import json
from django.conf import settings
# Navigate to https://www.dwolla.com/applications (production) or https://dashboard-sandbox.dwolla.com/applications (Sandbox) for your application key and secret.


class DwollaClient():
    """
    This is a basic client implementation for the Dwolla API
    """
    __instance = None

    _client = None

    _token = None

    @property
    def api_url(self):
        """
        retrieves the api url for the client to use


        Returns:
            str
        """
        if self._client.environment == 'sandbox':
            return 'https://api-sandbox.dwolla.com/'
        return 'https://api.dwolla.com/'

    @property
    def funding_source_url(self):
        """
        The endpoint for funding sources

        Returns:
            str
        """
        return '%sfunding-sources/' % self.api_url

    @property
    def customer_url(self):
        """
        the endpoint for customers
        Returns:
            str
        """
        return '%scustomers/' % self.api_url

    @property
    def token(self):
        """
        The token for this client

        Returns:
            str
        """
        return self._token

    @property
    def client(self):
        """
        The client object
        Returns:

        """
        return self._client

    def refresh(self):
        """
        Refreshes the client token
        """
        self._token = self.client.Auth.client()

    def __init__(self):
        """
        Initializes an instance of the DwollaClient
        """
        self._client = dwollav2.Client(key=settings.DWOLLA_KEY,
                                       secret=settings.DWOLLA_SECRET,
                                       environment='sandbox')  # optional - defaults to production
        self.refresh()

    @staticmethod
    def instance():
        """
        Singleton accessor for the client

        Returns:
            customer.dwolla.DwollaClient
        """
        if not DwollaClient.__instance:
            DwollaClient.__instance = DwollaClient()
        return DwollaClient.__instance


def dwolla_get_url(url):
    """
    A helper method for the DwollaClient to retreive any url

    Args:
        url (str): the url to retreive

    Returns:
        response
    """
    try:
        result = DwollaClient.instance().token.get(url)
        return result.body
    except Exception as e:
        logger.error("Could not get url: %s %s " % (url, e))
    return None


def dwolla_simulate_sandbox_transfers():
    """
    This method is used to simulate ACH transfers for the sandbox

    """
    result = DwollaClient.instance().token.post('sandbox-simulations')
    return result


def dwolla_create_user(user):
    """
    Takes a PSPUser and creates a user for them in the Dwolla API

    Args:
        user (customer.models.PSPUser): The PSPUser to create in the Dwolla API:

    Returns:
        bool: success of the operation

    """

    json = user.to_json()

    try:
        customer = DwollaClient.instance().token.post('customers', json)
        url = customer.headers['location']
        user.dwolla_url = url
        user.save()
        return True
    except Exception as e:
        logger.error("could not get customer location %s " % e)

    return False


def dwolla_update_user(user):
    """
    Takes a PSPUser and updates a user for them in the Dwolla API

    Args:
        user (customer.models.PSPUser): The PSPUser to update in the Dwolla API:

    Returns:
        bool: success of the operation
    """

    json = user.to_update_json()

    try:
        customer = DwollaClient.instance().token.post(
            'customers/%s' % user.dwolla_id, json)

        if customer.status == 200:
            return True
    except Exception as e:
        logger.error("could not get customer location %s " % e)

    return False


def dwolla_generate_funding_source_token(user):
    """
    Takes a user and generates a token to use.  That token is used to create a funding source for this user

    Args:
        user (customer.models.PSPUser): The PSPUser to create a token for in the creation of a funding source

    Returns:
        str: the token that was created
    """
    if user.dwolla_url:
        funding_token_req = '%s/iav-token' % user.dwolla_url
        try:
            request = DwollaClient.instance().token.post(funding_token_req)
            return request.body['token']
        except Exception as e:
            logger.error("could not get dwolla account funding token %s " % e)

    return None


def dwolla_get_user_balance(user):
    """
    Gets a balance for a user. Note that this is not functional in sandbox mode

    Args:
        user (customer.models.PSPUser): The PSPUser to create a token for in the creation of a funding source

    Returns:
        dict: a dictionary with balance information
    """
    items = dwolla_get_funding_sources(user)

    for item in items:
        if item['type'] == 'balance':
            return item

    return None


def dwolla_get_user_bank_accounts(user):
    """
    Gets a list of bank accounts for a user

    Args:
        user (customer.models.PSPUser): The PSPUser to create a token for in the creation of a funding source

    Returns:
        list: a list of bank accounts for a user
    """

    items = dwolla_get_funding_sources(user)

    to_return = []
    if items:
        for item in items:
            if item['type'] == 'bank':
                to_return.append(item)

    return to_return


def dwolla_get_funding_sources(user):
    """
    Gets a list of funding sources for a user

    Args:
        user (customer.models.PSPUser): The PSPUser to create a token for in the creation of a funding source

    Returns:
        list: A list of funding sources for a user
    """

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
    """
    Gets the balance of a users funding source.  Note that this does not work in sandbox mode.

    Args:
        funding_source (str): The funding source url to get the balance of

    Returns:
        dict: A dictionary with balance information
    """
    try:
        balance_url = funding_source['_links']['balance']['href']
        results = DwollaClient.instance().token.get(balance_url)

        return results.body

    except Exception as e:
        logger.error("could not get balance %s " % e)

    return {'balance': {'currency': 'USD', 'value': '0.00'}}


def dwolla_create_transfer(purchase):
    """
    Creates a purchase of crypto transfer from a user to the PSP

    Args:
        purchase (customer.models.Purchase): The Purchase object to use to determine what has been sent to the PSP

    Returns:
        dict: the transfer object that has been created
    """
    request_body = {
        '_links': {
            'source': {
                'href': '%s%s' % (DwollaClient.instance().funding_source_url, purchase.sender_account_id)
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

    transfer = DwollaClient.instance().token.post('transfers', request_body)

    return transfer


def dwolla_send_to_user(deposit):
    """
    Sends an amount of fiat to a user based on the parameters of the Deposit object sent to it.

    Args:
        deposit (customer.models.Deposit): The deposit to use to determine what to send to the user

    Returns:
        dict: the transfer object that has been created
    """
    request_body = {
        '_links': {
            'source': {
                'href': '%s%s' % (DwollaClient.instance().funding_source_url, deposit.sender_account_id)
            },
            'destination': {
                'href': '%s%s' % (DwollaClient.instance().funding_source_url, deposit.receiver_account_id)
            }
        },
        'amount': {
            'currency': 'USD',
            'value': "%0.2f" % (deposit.total,),
        },
        'correlationId': deposit.id,
    }

    transfer = DwollaClient.instance().token.post('transfers', request_body)

    return transfer


def dwolla_get_transfers(user):
    """
    Gets a list of all transfers associated with a user

    Args:
        user (customer.models.PSPUser): The PSPUser to create a token for in the creation of a funding source

    Returns:
        list: a list of all transfers associated with a user
    """

    url = '%s/transfers' % user.dwolla_url
    try:
        transferlist = DwollaClient.instance().token.get(url)
        return transferlist.body['_embedded']['transfers']

    except Exception as e:
        logger.error("could not get transfer list: %s " % e)

    return None
