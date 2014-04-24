# -*- coding: utf-8 -*-
from common.yandex import YMLGenerator
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand, CommandError
from django.template.defaultfilters import striptags
from django.utils.datastructures import SortedDict
from sorl.thumbnail import get_thumbnail
from frontend.models import Product, Category
from django.conf import settings


def tree_get():
    result = []
    tt = (Category.tree_get()).__iter__()
    level_off = 100000
    while 1:
        try:
            cat = next(tt)
            if cat.level > level_off:
                cat.state = 0
            elif cat.state == 0:
                level_off == cat.level
            else:
                level_off = 100000

            if cat.state:
                result.append(cat)

        except StopIteration:
            break
    return result

def yml_categories(info):
    yield {'id': 15, 'title' : u'Каталог'.encode('windows-1251')}

    for cat in tree_get():
        if cat.url_get().startswith('/catalog/'):
            yield {'id': cat.pk, 'parentId' : cat.parent_id, 'title': cat.title.encode('windows-1251')}


def clean(content):
    replace = {
        '&nbsp;': ' ',
        '&laquo;' : ' ',
        '&raquo;' : ' ',
        '&bull;' : ' ',
        '&ndash;' : ' '
    }

    for key, val in replace.iteritems():
        content = content.replace(key, val)

    return content

def yml_offers(info):

    for cat in tree_get():
        if cat.url_get().startswith('/catalog/'):
            for product in Product.active_objects.filter(category=cat):
                try:
                    picture = get_thumbnail(product.product_images_get()[0].image, '200x200').url
                except BaseException, e:
                    picture = ''
                    # picture = name = get_thumbnail(item.product.productimage_set.all()[0].image, '90x90').name
                yield {'price': float(product.price),
                       # 'currencyId': currency_map[product['price_1']['valyuta']],
                       'currencyId': 'RUR',
                       'name': product.title.encode('windows-1251'),
                       'categoryId': cat.id,
                       'picture': '%s%s' % (info['url'], picture),
                       # 'vendor': vendor.title.encode('windows-1251'),
                       'url': '%s%s' % (info['url'], product.url_get(cat=cat)),
                       'id': product.pk,
                       'delivery': 'true',
                       'description': clean(striptags(product.content)).encode('windows-1251'),
                       'available': 'true'}


def yml_generate():
    yml_gen = YMLGenerator()

    info = {'url': 'http://www.flowershop.ru',
            'name': 'flowershop.ru',
            'company': 'flowershop.ru',
            'platform': 'vestlite',
            'version': '2.0',
            'agency': 'vestlite',
            'email': 'vadim@vestlite.com'}

    currencies = [{'id': 'USD', 'rate': 'CBRF'},
                  {'id': 'EUR', 'rate': 'CBRF'},
    ]

    return yml_gen.generate('%s/yml.xml' % settings.MEDIA_ROOT,
                            info=info,
                            currencies=currencies,
                            categories=yml_categories(info=info),
                            offers=yml_offers(info))


class Command(BaseCommand):
    def handle(self, *args, **options):
        # from fs_import import yml_generate, yml_generate_ua, yml_generate_kz
        yml_generate()
        # yml_generate_kz()
        # yml_generate_ua()