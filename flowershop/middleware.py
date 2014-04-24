from common.cachedtree import CacheTree
from django.db.models import Q
import re
from frontend.models import Category, SimplePage, DeliveryTime, DeliveryType, City, PaymentType
import logging
logger = logging.getLogger('middleware')

class MiddlewareCachedTree(object):
    def process_request(self, request):
        request.cached_tree = CacheTree(Category.tree_get(params={'state':True}), url=request.path)


class MiddlewareSimplePage(object):
    def process_request(self, request):
        try:
            if not hasattr(request, 'simple_page'):
                request.simple_page = None

            url = re.sub(r'/+', '/', '/%s/' % request.path_info.strip('/'), re.IGNORECASE)
            sps = []
            #check_re

            #check if this seller subdomain
            #qset = SimplePage.site_objects.filter(url=url, state=True)
            #ahtung distinct!!!
            qset = SimplePage.active_objects.filter(Q(url=url) | Q(category__url=url)| Q(url=request.path.lstrip('/')), state=True).distinct()

            for idx, sp in enumerate(qset):
                sps.append(sp)

            if len(sps):
                request.simple_page = sps #deprecated
                request.vt_sps = sps
        except SimplePage.DoesNotExist:
            request.simple_page = None


class MiddlewareCategory(object):
    def process_request(self, request):

        try:
            request.vt_category = Category.objects.get(url=request.path)
        except BaseException, e:
            request.vt_category = None


def basket_init(request):
    save = False
    if not 'basket' in request.session:
        request.session['basket'] = {}
        save = True

    if not 'products' in request.session['basket']:
        request.session['basket']['products'] = {}
        request.session['basket']['qty'] = 0
        request.session['basket']['sum'] = 0
        request.session['basket']['sum_dsc'] = 0


        save = True

    if not 'delivery_info' in request.session:
        try:
            request.session['delivery_info'] = {
                'delivery_time': DeliveryTime.active_objects.all()[0].pk,
                'delivery_type': DeliveryType.active_objects.all()[0].pk,
                'city': City.active_objects.all()[0].pk,
                'payment_type' : PaymentType.active_objects.all()[0].pk,
                'another_city' : '',
                'distance' : 0.0

            }
            save = True
        except IndexError:
            logger.debug('delivery info error')

    if save:
        request.session.save()

    return request.session['basket'], request.session.get('delivery_info')


class MiddlewareBasket(object):
    def process_request(self, request):
        request.vt_basket, request.vt_delivery_info = basket_init(request)
