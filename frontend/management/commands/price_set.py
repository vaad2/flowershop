# -*- coding: utf-8 -*-
import logging
from common.db import qset_to_dict
from common.user_agent import random_user_agent
from django.core.management.base import BaseCommand, CommandError
logger = logging.getLogger('flowershop.commands')
from pyquery import PyQuery
import requests


# proxy_data = {'headers': {'User-Agent': random_user_agent()}, 'cookies': {'yandex_gid': '213'}}
# if proxy.host !=  'localhost':
#     proxy_data.update({'proxies': {'http': 'http://%s' % proxy.host}})
from frontend.models import LinkedPrice, Settings


class Command(BaseCommand):
    def handle(self, *args, **options):
        st = qset_to_dict(Settings.objects.all(), 'name')
        linked_discount = float(st['linked_discount'].value)

        proxy_data = {'headers': {'User-Agent': random_user_agent()}}
        for lp in LinkedPrice.active_objects.select_related('product', 'linked_site').all():
            s = requests.session()

            proxy_data['headers']['User-Agent'] = random_user_agent()
            res = s.get(lp.url, **proxy_data)

            try:
                pq = PyQuery(res.content)
                price = pq('[itemprop="offers"] .price')
                if len(price):
                    price = float(price.text().replace(' ', '').replace(u'p.', ''))
                    lp.price = price
                    lp.save()

                    price += linked_discount
                    if lp.product.price_stop <= price and lp.product.price > lp.price:
                        lp.product.price = price
                        lp.product.save()
            except BaseException, e:
                logger.debug('cant find price %s' % lp.url)



         # proxy_data['headers']['User-Agent'] = random_user_agent()
         #
         #            url = 'http://market.yandex.ru/search.xml?%s' % urlencode(
         #                {'text': '%s host:%s' % (pn, site.host), 'cvredirect': 2})
         #
         #            publish({'event': 'msg',
         #                     'data': '%s try search on yandex.ru: <a href="%s" target="_blank">%s</a>' % (
         #                         site.host, url, pn)})
         #
         #            res = s.get(url, **proxy_data)
