from blockchain.models import Price


def crypto_prices(request):
    ctx = {}
    for price in Price.objects.all():
        ctx['price_%s' % price.asset] = price.usd
    return ctx
