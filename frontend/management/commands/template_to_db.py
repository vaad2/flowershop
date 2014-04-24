# -*- coding: utf-8 -*-
import logging
from common.models import SiteTemplate
from common.std import ex_find_template
from django.core.management.base import BaseCommand, CommandError
import os

logger = logging.getLogger('flowershop.commands')
from django.conf import settings

class Command(BaseCommand):
    def handle(self, *args, **options):
        paths = [['%s/frontend/templates/frontend' % settings.PROJECT_ROOT, 'frontend/'],
                 ['%s/frontend/templates/ajax_frontend' % settings.PROJECT_ROOT, 'ajax_frontend/'],
                 ['%s/templates' % settings.PROJECT_ROOT, '']]

        for path in paths:
            for item in os.listdir(path[0]):
                try:
                    name = '%s%s' % (path[1], item)
                    if SiteTemplate.objects.filter(name=name).exists():
                        continue

                    content = ex_find_template(name, ['common.loaders.load_template_source'])[0]
                    SiteTemplate.objects.create(user_id=1,name=name, content = content)
                except BaseException, e:
                    logger.debug('tmpl not found %s' % e)
