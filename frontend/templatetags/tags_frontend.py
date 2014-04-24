import logging
import urllib
from common.std import model_class_get
from django.template import Library, Node, TemplateSyntaxError
from django.template.loader import render_to_string
from frontend.models import Category

logger = logging.getLogger('flowershop.templatetags')

register = Library()


@register.simple_tag(takes_context=True)
def tag_ctree_children_get(context, *args, **kwargs):
    try:
        context[kwargs['var']] = context['cached_tree'][kwargs['pk']].children(**kwargs)
    except BaseException, e:
        logger.debug('tag_ctree_children_get %s' % e)

    return ''


@register.simple_tag(takes_context=True)
def tag_paginator_params(context, *args, **kwargs):
    paginator = args[0]
    exclude = kwargs.get('exclude', '').split(',')
    var_name = kwargs.get('var_name', 'vt_paginator_url')
    items = {}

    for key, val in paginator.params.iteritems():
        if key in exclude:
            continue

        if isinstance(val, str) or isinstance(val, unicode):
            items[key] = val.encode('utf-8')
        else:
            items[key] = val

    context[var_name] = urllib.urlencode(items)

    return ''


@register.filter
def price(val):
    try:
        return int(round(val))
    except BaseException, e:
        logger.debug('wrong price filter param %s' % e)
        return 0
