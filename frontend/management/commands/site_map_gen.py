# -*- coding: utf-8 -*-
import logging
from common.models import SiteTemplate
from common.std import ex_find_template, SiteMapGenerator
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand, CommandError
from django.core.urlresolvers import reverse
from django.db.models import Q
import os
from frontend.models import Category, SimplePage

logger = logging.getLogger('flowershop.commands')
from django.conf import settings

class Command(BaseCommand):
    def handle(self, *args, **options):
        sitemap_gen = SiteMapGenerator()

        site = Site.objects.all()[0]
        domain = 'http://www.%s' % site.domain

        def urls():
            exists = {}
            for cat in Category.active_objects.all():
                url = cat.url_get()
                if len(url):
                    if not url.startswith('/'):
                        url = '/%s' % url
                    yield {'loc': '%s%s' % (domain, url), 'priority': 1, 'changefreq': 'daily'}

                exists[url] = True

                for product in cat.product_set.filter(state=True):
                    url = product.url_get(cat)
                    if not url.startswith('/'):
                        url = '/%s' % url

                    yield {'loc': '%s%s' % (domain, url),
                           'priority': 1,
                           'changefreq': 'daily'}
                    exists[url] = True


            query = Q(url__istartswith='yandex') | Q(url__istartswith='wmail') | Q(url__istartswith='google')
            for page in SimplePage.active_objects.all().exclude(query):
                url = page.url

                if page.url and not page.url in exists:
                    if not url.startswith('/'):
                        url = '/%s' % url

                    yield {'loc': '%s%s' % (domain, url), 'priority': 1, 'changefreq': 'daily'}

        sitemap_gen.generate('%s/sitemap.xml' % settings.MEDIA_ROOT, urls=urls())

