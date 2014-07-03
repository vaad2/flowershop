# -*- coding: utf-8 -*-
from urllib import urlencode, unquote
from common.db import qset_to_dict
from common.http import ujson_response
from common.views import MixinBase, ExMultipleObjectMixin, AjaxView
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.staticfiles import finders
from django.core.urlresolvers import reverse, reverse_lazy
from django.db.models import Q, F
from django.forms import model_to_dict
from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.utils.datastructures import SortedDict
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, DetailView, ListView, FormView, RedirectView, View
from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

import logging
import ujson
from payment import VTRobokassa
from os.path import basename
import posixpath
from sorl.thumbnail import get_thumbnail
from frontend.ajax_views import sms_send
from frontend.models import *
# , Delivery, DeliveryGroup

logger = logging.getLogger('flowershop.views')


def products_photos_get(qset):
    ids_map = SortedDict()
    for product in qset:
        ids_map[product.pk] = product

    for img in ProductImage.active_objects.filter(product__in=ids_map.keys()).order_by('pos'):
        product = ids_map[img.product_id]
        if not hasattr(product, 'images'):
            product.images = []

        product.images.append(img)

    return ids_map.values()


class ViewIndex(MixinBase, TemplateView):
    def get_context_data(self, **kwargs):
        context = super(ViewIndex, self).get_context_data(**kwargs)

        try:
            context['slider'] = Slider.active_objects.get(slug='index')
        except Slider.DoesNotExist:
            logger.debug('slider not found')

        st = qset_to_dict(Settings.objects.all(), key='name')

        index_news = 4
        index_products = 8
        if 'index_news' in st:
            index_news = st['index_news'].value

        if 'index_products' in st:
            index_products = st['index_products'].value

        context['news'] = News.active_objects.all()[0:int(index_news)]
        context['products'] = products_photos_get(
            Product.active_objects.all().order_by('-popular_cnt')[0:int(index_products)])

        return context


class ViewNewsItem(MixinBase, DetailView):
    def get_breadcrumbs(self):
        return [{'title': 'Новости', 'url': reverse('frontend:view_news')},
                {'title': self.object.title}]

    def get_queryset(self):
        return News.active_objects.all()


class ViewProducts(AjaxView, ExMultipleObjectMixin, ListView):
    paginate_by = 16

    def get_breadcrumbs(self):
        if self.cat:
            return self.cat.parents_get(include_self=True, min_level=1)
        return [{'title': 'Каталог'}]


    def get_queryset(self, skip_price=False):
        qset = Product.active_objects.all()

        if self.cat:
            qset = qset.filter(category__path__istartswith=self.cat.path).order_by(self.sort_field)

        if self.query:
            qset = qset.filter(Q(title__icontains=self.query) | Q(content__icontains=self.query) |
                               Q(consist__icontains=self.query))

        if not skip_price:
            if 'price_from' in self.filter_params:
                qset = qset.filter(price__gte=self.filter_params['price_from'])
            if 'price_to' in self.filter_params:
                qset = qset.filter(price__lte=self.filter_params['price_to'])

        return qset


    def get_context_data(self, **kwargs):
        params = dict(self.order_params)
        params.update(self.filter_params)
        kwargs['params'] = params

        context = super(ViewProducts, self).get_context_data(**kwargs)
        context['catalog'] = self.cat

        context['order_params'] = self.order_params

        qset = self.get_queryset(skip_price=True)

        if qset.count():
            context['price_min'] = qset.order_by('price')[0].price
            context['price_max'] = qset.order_by('-price')[0].price

            if not 'price_from' in self.filter_params:
                self.filter_params['price_from'] = context['price_min']

            if not 'price_to' in self.filter_params:
                self.filter_params['price_to'] = context['price_max']

            for key in ['price_from', 'price_to']:
                self.filter_params[key] = int(self.filter_params[key])
            context['filter_params'] = self.filter_params

            context['products'] = products_photos_get(context['object_list'])

        return context

    def dispatch(self, request, *args, **kwargs):
        try:
            self.cat = Category.objects.get(url=request.path)
        except Category.DoesNotExist:
            self.cat = None

        self.query = request.REQUEST.get('query', '')

        map_order = {
            'asc': '',
            'desc': '-'
        }

        map_sort = {
            'title': 'title',
            'price': 'price',
            'popular': 'popular_cnt'
        }

        order = request.REQUEST.get('order', 'asc')

        if 'switch' in request.REQUEST:
            order = 'desc' if order == 'asc' else 'asc'

        self.order_params = {
            'sort': request.REQUEST.get('sort', 'title'),
            'order': order
        }

        self.filter_params = {}

        if 'price_from' in request.REQUEST:
            self.filter_params['price_from'] = int(request.REQUEST['price_from'])

        if 'price_to' in request.REQUEST:
            self.filter_params['price_to'] = int(request.REQUEST['price_to'])

        self.sort_field = '%s%s' % (map_order[order], map_sort[self.order_params['sort']])

        return super(ViewProducts, self).dispatch(request, *args, **kwargs)


class ViewProduct(MixinBase, DetailView):
    def get_queryset(self):
        return Product.active_objects.all()

    def get_breadcrumbs(self):
        dt = self.object.category.through.objects.select_related('category').filter(product=self.object,
                                                                                    category__path__istartswith=self.cat.path)[
            0]
        bc = list(dt.category.parents_get(include_self=True, min_level=1))
        bc.append(self.object)
        return bc

    def dispatch(self, request, *args, **kwargs):
        self.cat = Category.objects.get(url='%s/' % '/'.join(request.path.split('/')[:-3]))

        return super(ViewProduct, self).dispatch(request, *args, **kwargs)


class ViewNews(MixinBase, ExMultipleObjectMixin, ListView):
    paginate_by = 16

    def get_breadcrumbs(self):
        return [{'title': 'Новости'}]

    def get_queryset(self):
        return News.active_objects.all()


class ViewCategory(MixinBase, DetailView):
    model = Category

    #
    # if not request.profile or (request.profile and request.profile.price_column == 1):
    #     val, next, pc = Discount.discount_get(summary['sum'])
    #     summary['discount_val'] = round(val * summary['sum_wds'] / 100, 2)
    #     summary['discount_next'] = next
    #     summary['discount_next_str'] = pc
    #     summary['discount_str'] = '%s%%' % int(val)


def basket_recalc(request):
    products = SortedDict()
    basket = request.vt_basket['products']
    price_sum = 0
    variants = {}
    full_qty = 0

    for val in basket.itervalues():
        for key, qty in val.iteritems():
            variants[key] = qty

    variant_products = qset_to_dict(ProductVariant.active_objects.filter(pk__in=variants.keys()))

    for product in Product.active_objects.filter(pk__in=basket.keys()):
        bp = basket[unicode(product.pk)]

        product.variants = SortedDict()

        for key, qty in bp.iteritems():  #cycle on variants in basket
            key = int(key)
            if key in variant_products:
                vpr = variant_products[key].price_get()
                variant_title = variant_products[key].title
            else:
                vpr = product.price_get()
                variant_title = product.title

            vps = vpr * qty
            price_sum += vps
            full_qty += qty

            product.variants[key] = {
                'qty': qty,
                'sum': vps,
                'vpr': vpr,
                'variant_title': variant_title
            }

        products[product.pk] = product

    request.vt_basket['sum'] = price_sum
    request.vt_basket['qty'] = full_qty

    pc_curr, dt_next, pc_next = Discount.discount_get(price_sum)

    dsc = price_sum * pc_curr / 100
    request.vt_basket['dsc_sum'] = price_sum - dsc

    request.session.save()

    return {
               'sum': price_sum,
               'qty': full_qty,
               'dsc': dsc,
               'dsc_sum': request.vt_basket['dsc_sum'],
               'pc_curr': pc_curr,
               'dt_next': dt_next,  #delta_next
               'pc_next': pc_next

           }, products


# class ViewCart(AjaxView, TemplateView):
#     def cmd_cities_get(self, request):
#         cities = []
#         for city in City.active_objects.all():
#             cities.append(model_to_dict(city))
#
#
#         return ujson_response(cities)
#
#     def cmd_city_set(self, request):
#
#         return ujson_response({'success' : True})



class ViewCart(AjaxView, TemplateView):
    json_handler = ujson_response
    breadcrumbs = [{'title': 'Корзина'}]

    def cmd_cart_add(self, request, *args, **kwargs):
        pk = request.REQUEST['pk']
        pk_variant = request.REQUEST.get('pk_variant', 0)

        if not pk in request.vt_basket['products']:
            request.vt_basket['products'][pk] = {pk_variant: 0}

        if not pk_variant in request.vt_basket['products'][pk]:
            request.vt_basket['products'][pk][pk_variant] = 0

        request.vt_basket['products'][pk][pk_variant] += 1

        basket_recalc(request)

        return True, {'sum': request.vt_basket['sum'], 'qty': request.vt_basket['qty']}

    def cmd_update(self, request):
        data = ujson.loads(request.REQUEST['data'])
        vt_basket = request.vt_basket

        for item in data:
            qty = int(item['qty'])
            if qty <= 0:
                try:
                    del vt_basket['products'][unicode(item['pk'])][unicode(item['pk_variant'])]
                except BaseException, e:
                    logger.debug(e)
            else:
                try:

                    vt_basket['products'][unicode(item['pk'])][unicode(item['pk_variant'])] = qty
                except BaseException, e:
                    logger.debug(e)

        products = []
        result, bproducts = basket_recalc(request)
        for product in bproducts.itervalues():
            for pk_variant, variant in product.variants.iteritems():
                products.append({'pk': product.pk,
                                 'pk_variant': pk_variant,
                                 'qty': variant['qty'],
                                 'sum': variant['sum']})

        result['products'] = products

        result['summary'] = self._summary_recalc()

        return True, result


    # def _cmd_update_qty(self, request):
    #     pk = request.REQUEST['pk']
    #     qty = int(request.REQUEST['qty'])
    #
    #     if qty <= 0:
    #         try:
    #             del request.vt_basket['products'][pk]
    #         except BaseException, e:
    #             logger.debug(e)
    #     else:
    #         try:
    #             request.vt_basket['products'][pk] = qty
    #         except BaseException, e:
    #             logger.debug(e)
    #
    #     basket_recalc(request)
    #
    #     return True, {'sum': request.vt_basket['sum'], 'qty': request.vt_basket['qty']}


    def _delivery_form_class_get(self):
        class _Form(forms.Form):
            city = forms.ModelChoiceField(label=_('delivery city'), queryset=City.active_objects.all(),
                                          empty_label=None)
            delivery_type = forms.ModelChoiceField(label=_('delivery type'),
                                                   queryset=DeliveryType.active_objects.all(), empty_label=None,
                                                   widget=forms.RadioSelect)
            delivery_time = forms.ModelChoiceField(label=_('delivery time'), queryset=DeliveryTime.active_objects.all(),
                                                   empty_label=None,
                                                   widget=forms.RadioSelect)

        return _Form

    def _client_form_class_get(self):
        class _Form(forms.ModelForm):
            # def clean_receiver_date_time(self):
            #     return datetime.datetime.strptime(self.cleaned_data['receiver_date_time'], "%d.%m.%y %H:%M")

            class Meta:
                model = ShopOrder
                fields = ['client_name', 'client_phone', 'client_email', 'client_comment', 'receiver_name',
                          'receiver_address', 'receiver_date_time', 'receiver_comment']

        return _Form

    def cmd_order_send(self, request):
        di = request.session['delivery_info']
        bsk = request.session['basket']
        dc_data = dict(request.REQUEST)
        dc_data.update(di)

        try:
            dc_data['payment_type'] = PaymentType.active_objects.get(pk=dc_data['payment_type'])
            dc_data['delivery_type'] = DeliveryType.active_objects.get(pk=dc_data['delivery_type'])
            dc_data['delivery_time'] = DeliveryTime.active_objects.get(pk=dc_data['delivery_time'])
            dc_data['city'] = City.active_objects.get(pk=dc_data['city'])

        except BaseException, e:
            logger.debug('wrong params %s' % e)
            return False

        result, products = basket_recalc(request)

        form = self._client_form_class_get()(data=dc_data)
        if bsk['qty'] and form.is_valid():
            shop_order = form.save(commit=False)
            shop_order.payment_type = dc_data['payment_type']
            shop_order.delivery_type = dc_data['delivery_type']
            shop_order.delivery_time = dc_data['delivery_time']
            shop_order.city = dc_data['city']
            shop_order.sum = bsk['sum']
            shop_order.discount = result['dsc']
            shop_order.delivery_sum, shop_order.summary = self._summary_recalc()
            shop_order.qty = bsk['qty']

            shop_order.save()

            for product in products.itervalues():
                product.popular_cnt += 1
                product.save()
                for pvk, pv in product.variants.iteritems():
                    if not pvk:
                        pvk = None

                    ShopOrderItem.objects.create(shop_order=shop_order,
                                                 product=product,
                                                 product_variant_id=pvk,
                                                 qty=pv['qty'],
                                                 sum=pv['sum'])

            bsk['products'] = {}
            bsk['sum'] = 0
            bsk['qty'] = 0
            #
            request.session.save()

            sms_send(u'Сформирован заказ N%s на %s р. Телефон %s, имя %s, email %s ' % (
                shop_order.pk,
                shop_order.summary,
                shop_order.client_phone,
                shop_order.client_name,
                shop_order.client_email
            ))

            st = qset_to_dict(Settings.objects.all(), key='name')
            mail_manager = st['mail_manager'].value if 'mail_manager' in st else 'vadim@vestlite.com'

            mail_send_order(shop_order.pk, to=shop_order.client_email)
            mail_send_order(shop_order.pk, to=mail_manager,
                            subject=u'В магазине flowershop.ru сделан заказ №%s' % shop_order.pk)

            return True, {'redirect': reverse('frontend:view_confirm', kwargs={'pk': shop_order.pk})}

        return False


    def _summary_recalc(self):
        di = self.request.session['delivery_info']

        if di['city'] == 3:
            val = float(Settings.objects.get(name='price_for_km').value)
            sum_city = val * di['distance']
        else:
            sum_city = City.active_objects.get(pk=di['city']).price

        sum_delivery = sum_city + DeliveryType.active_objects.get(pk=di['delivery_type']).price + \
                       DeliveryTime.active_objects.get(pk=di['delivery_time']).price

        try:
            pt = PaymentType.active_objects.get(pk=di.get('payment_type', 1)).price
        except PaymentType.DoesNotExist:
            pt = 0

        return sum_delivery, sum_delivery + self.request.vt_basket['dsc_sum'] + pt

    def cmd_payment_type_set(self, request, *args, **kwargs):
        self.request.session['delivery_info']['payment_type'] = PaymentType.active_objects.get(
            pk=request.REQUEST['pk']).pk
        self.request.session.save()
        smd, smm = self._summary_recalc()
        return True, smm

    def cmd_delivery_recalc(self, request, *args, **kwargs):
        di = self.request.session['delivery_info']
        rq = request.REQUEST

        try:
            di['delivery_type'] = DeliveryType.active_objects.get(pk=rq['delivery_type']).pk
        except DeliveryType.DoesNotExist:
            di['delivery_type'] = DeliveryType.active_objects.all()[0].pk

        try:
            di['delivery_time'] = DeliveryTime.active_objects.get(pk=rq['delivery_time']).pk
        except DeliveryType.DoesNotExist:
            di['delivery_time'] = DeliveryTime.active_objects.all()[0].pk

        try:
            di['city'] = City.active_objects.get(pk=rq['city']).pk
        except DeliveryType.DoesNotExist:
            di['city'] = City.active_objects.all()[0].pk

        if di['city'] == 3:  #another city
            di['another_city'] = rq['another_city']

            try:
                di['distance'] = float(rq['distance'])
            except BaseException, e:
                di['distance'] = 0.0

        request.session.save()

        sum_delivery, summary = self._summary_recalc()

        return True, summary


    def get_context_data(self, **kwargs):
        context = super(ViewCart, self).get_context_data(**kwargs)

        result, products = basket_recalc(self.request)
        context.update(result)
        context['products'] = products

        for img in ProductImage.active_objects.filter(product__in=products.keys()):
            product = products[img.product_id]
            if not hasattr(product, 'images'):
                product.images = []

            product.images.append(img)

        context['delivery_form'] = self._delivery_form_class_get()(initial=self.request.vt_delivery_info)
        context['client_form'] = self._client_form_class_get()()

        context['payment_types'] = []

        di = self.request.session['delivery_info']

        for pt in PaymentType.active_objects.all():
            pt.active = unicode(pt.pk) == unicode(di.get('payment_type', 1))

            context['payment_types'].append(pt)

        context['delivery_sum'], context['summary'] = self._summary_recalc()

        return context


class ViewSearch(ViewProducts):
    template_name = 'frontend/view_products.html'
    paginate_by = 2

    def get_queryset(self):
        qset = Product.active_objects.all()

        if self.query:
            qset = qset.filter(Q(title__icontains=self.query) | Q(content__icontains=self.query) |
                               Q(consist__icontains=self.query))

        return qset

    def get_breadcrumbs(self):
        return [{'title': 'Поиск'}]

    def cmd_search(self, request):
        result = {'query': self.query, 'suggestions': []}

        if len(self.query) > 1:
            for product in self.get_queryset():
                result['suggestions'].append(
                    {
                        'value': product.title,
                        'data': product.url_get()
                    })

        return ujson_response(result)


class ViewAuth(MixinBase, TemplateView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            return redirect('frontend:view_cabinet')
        return super(ViewAuth, self).dispatch(request, *args, **kwargs)

    def get_breadcrumbs(self):
        return [{'title': 'Личный кабинет'}]


def auth_pass(user):
    return user.is_authenticated() and user.is_active


class ViewLogout(RedirectView):
    permanent = False

    def get_redirect_url(self, **kwargs):
        logout(self.request)
        return reverse('frontend:view_cabinet')


class MixinAuth(MixinBase):
    @method_decorator(user_passes_test(auth_pass, login_url='/auth/'))
    def dispatch(self, request, *args, **kwargs):
        return super(MixinAuth, self).dispatch(request, *args, **kwargs)


class ViewCabinet(AjaxView, FormView):
    def get_form_class(self):
        request = self.request

        class _Form(forms.Form):
            email = forms.EmailField(label=_('email'))
            password_old = forms.CharField(label=_('password old'), widget=forms.PasswordInput, required=False)
            password_new = forms.CharField(label=_('password new'), widget=forms.PasswordInput, required=False)
            password_new_repeat = forms.CharField(label=_('password new repeat'), widget=forms.PasswordInput,
                                                  required=False)
            username = forms.CharField(label=_('username'))
            phone = forms.CharField(label=_('phone'))

            def clean(self):
                cd = super(_Form, self).clean()
                psw_old = cd.get('password_old', '')
                psw_new = cd.get('password_new', '')
                psw_new_rp = cd.get('password_new_repeat', '')

                if len(psw_old) or len(psw_new) or len(psw_new_rp):
                    if not len(psw_new):
                        raise forms.ValidationError(_('password new field is required.'))

                    if not len(psw_new_rp):
                        raise forms.ValidationError(_('password new repeat field is required.'))

                    if not check_password(psw_old, request.user.password):
                        raise forms.ValidationError(_('password old field is wrong.'))

                    if psw_new != psw_new_rp:
                        raise forms.ValidationError(_('passwords not same'))

                if User.objects.filter(email=cd.get('email')).exclude(id=request.user.pk).exists():
                    raise forms.ValidationError(_('user with same email exist'))

                return cd

        return _Form

    def form_valid(self, form):
        user = self.request.user
        userprofile = user.userprofile
        cd = form.cleaned_data

        if len(cd['password_old']):
            user.set_password(cd['password_new'])

        user.email = cd['email']
        user.username = cd['email']

        userprofile.phone = cd['phone']
        userprofile.username = cd['username']

        user.save()
        userprofile.save()

        return True


    def get_context_data(self, **kwargs):
        context = super(ViewCabinet, self).get_context_data(**kwargs)
        context['shop_orders'] = ShopOrder.active_objects.filter(user=self.request.user)
        return context

    def get_initial(self):
        userprofile = self.request.user.userprofile
        return {'phone': userprofile.phone, 'username': userprofile.username, 'email': self.request.user.email}

    def get_breadcrumbs(self):
        return [{'title': 'Личный кабинет'}]

    @method_decorator(user_passes_test(auth_pass, login_url='/auth/'))
    def dispatch(self, request, *args, **kwargs):
        return super(ViewCabinet, self).dispatch(request, *args, **kwargs)


def robokassa_get():
    st = qset_to_dict(Settings.objects.all(), 'name')

    robokassa_test_mode = False
    if 'robokassa_test_mode' in st:
        robokassa_test_mode = bool(st['robokassa_test_mode'].value)

    robo = VTRobokassa(TestMode=robokassa_test_mode,
                       MerchantLogin=st['robokassa_login'].value,
                       MerchantPass1=st['robokassa_pass1'].value,
                       MerchantPass2=st['robokassa_pass2'].value)

    return robo


class ViewRobokassaConfirm(View):
    def dispatch(self, request, *args, **kwargs):
        rq = request.REQUEST

        out_sum = rq['OutSum']
        inv_id = rq['InvId']
        crc = rq['SignatureValue']

        robo = robokassa_get()
        if robo.pay_confirm(**self.request.REQUEST):
            ShopOrder.active_objects.filter(pk=inv_id).update(payment_status=True)

            return HttpResponse('OK%s' % inv_id)
        return HttpResponse('Failed%s' % inv_id)


class ViewRobokassaResult(MixinBase, TemplateView):
    def get_context_data(self, **kwargs):
        context = super(ViewRobokassaResult, self).get_context_data(**kwargs)
        rq = dict(self.request.REQUEST)
        robo = robokassa_get()
        order = ShopOrder.active_objects.get(pk=rq['InvId'])

        context['inv_id'] = order.pk
        context['success'] = order.payment_status and robo.pay_result(**rq)

        return context


class ViewRobokassaFail(MixinBase, TemplateView):
    pass


class ViewConfirm(MixinBase, DetailView):
    # def get_initial(self):
    #     return {'OutSum': self.order.summary,
    #             'InvId': self.order.pk,
    #             'Desc': 'order',
    #             'Email': self.order.client_email}

    def get_context_data(self, **kwargs):
        context = super(ViewConfirm, self).get_context_data(**kwargs)
        robo = robokassa_get()
        order = context['object']

        url = robo.pay_data(**{
            'OutSum': order.summary,
            'InvId': order.pk,
            'Desc': 'robo'

        })

        context['robo_link'] = url

        return context

    # def dispatch(self, request, *args, **kwargs):
    #     self.order = ShopOrder.active_objects.get(pk=self.kwargs['pk'])
    #     return super(ViewConfirm, self).dispatch(request, *args, **kwargs)


    def get_object(self, queryset=None):
        return ShopOrder.active_objects.get(pk=self.kwargs['pk'])


class ViewOrder(MixinAuth, ListView):
    def get_breadcrumbs(self):
        return [{'title': 'заказ'}]

    def get_context_data(self, **kwargs):
        context = super(ViewOrder, self).get_context_data(**kwargs)
        context['order'] = self.order
        return context

    def get_queryset(self):
        return self.order.shoporderitem_set.filter(state=1)

    def dispatch(self, request, *args, **kwargs):
        self.order = ShopOrder.active_objects.get(pk=kwargs['order_pk'])
        return super(ViewOrder, self).dispatch(request, *args, **kwargs)


def static_path_get(path):
    normalized_path = posixpath.normpath(unquote(path)).lstrip('/')
    absolute_path = finders.find(normalized_path)
    return absolute_path


from email.mime.image import MIMEImage
from email.mime.multipart import *
from email.mime.text import MIMEText


def mail_send(**kwargs):
    # Define these once; use them twice!

    strFrom = kwargs.get('email_from', settings.DEFAULT_FROM_EMAIL)
    strTo = kwargs['to']

    # Create the root message and fill in the from, to, and subject headers
    msgRoot = MIMEMultipart('related')
    msgRoot['Subject'] = kwargs.get('subject', u'Вы сделали заказ в магазине "Мир Букета"')
    msgRoot['From'] = strFrom
    msgRoot['To'] = strTo

    # msgRoot.preamble = kwargs.get('preamble', 'This is a multi-part message in MIME format.')

    # Encapsulate the plain and HTML versions of the message body in an
    # 'alternative' part, so message agents can decide which they want to display.
    msgAlternative = MIMEMultipart('alternative')
    msgRoot.attach(msgAlternative)

    # We reference the image in the IMG SRC attribute by the ID we give it below
    body = render_to_string(kwargs['tpl'], kwargs.get('context', {}))

    msgText = MIMEText(body.encode('utf-8'), 'html', 'utf-8')
    msgAlternative.attach(msgText)

    # This example assumes the image is in the current directory
    #{'path':'', 'content_id' : 'cid')
    for img in kwargs.get('images', []):
        try:
            fp = open(img['path'], 'rb')
            msgImage = MIMEImage(fp.read())
            fp.close()

            # Define the image's ID as referenced above

            msgImage.add_header('Content-ID', '<%s>' % img['content_id'])
            msgRoot.attach(msgImage)
        except BaseException, e:
            logger.debug('wrong attachment %s' % e)


    # Send the email (this example assumes SMTP authentication is required)
    import smtplib

    smtp = smtplib.SMTP()
    smtp.connect(settings.EMAIL_HOST, settings.EMAIL_PORT)

    smtp.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
    senderrs = smtp.sendmail(strFrom, strTo, msgRoot.as_string())

    smtp.quit()


def media_path_get(path):
    return '%s/%s' % (settings.MEDIA_ROOT, path)


def mail_send_order(pk, **kwargs):
    context = {}

    images = [{
                  'path': media_path_get(u'logo.png'),
                  'content_id': u'logo.png'
              }, {
                  'path': media_path_get(u'ico-phone.png'),
                  'content_id': u'ico-phone.png'
              }, {
                  'path': media_path_get(u'ico-time.png'),
                  'content_id': u'ico-time.png'
              }]

    context['cid_logo'] = u'cid:logo.png'
    context['cid_phone'] = u'cid:ico-phone.png'
    context['cid_time'] = u'cid:ico-time.png'

    items = []

    # cid:mail-splitter.png
    context['order'] = ShopOrder.objects.get(pk=pk)
    for item in context['order'].shoporderitem_set.select_related('product', 'product_variant'):
        title = item.product_variant.title if item.product_variant else item.product.title

        try:
            name = get_thumbnail(item.product.productimage_set.all()[0].image, '90x90').name

            items.append({
                'title': title,

                'qty': item.qty,
                'sum': item.sum,
                'cid': 'cid:%s' % basename(name)
            })

            images.append({
                'path': media_path_get(name),
                'content_id': basename(name)
            })

        except BaseException, e:
            items.append({
                'title': title,
                'qty': item.qty,
                'sum': item.sum,
                # 'cid': 'cid:%s' % basename(name)
            })

    context['items'] = items

    kkwargs = {
        'subject': u'Вы сделали заказ №%s в магазине "Мир Букета"' % context['order'].pk,
        'context': context,
        'images': images,
        'to': 'vadim@vestlite.com'
    }

    kkwargs.update(kwargs)

    mail_send(tpl='frontend/inc_mail_order.html', **kkwargs)


class ViewTestEmail(MixinBase, DetailView):
    template_name = 'frontend/mail_order.html'

    def get_object(self, queryset=None):
        return ShopOrder.active_objects.get(pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super(ViewTestEmail, self).get_context_data(**kwargs)

        context['order'] = context['object']

        # get_thumbnail(item.image, '890x518').url,
        # context['cid_logo'] = get_thumbnail(static_path_get(u'img/logo.png'), '222x48').url
        # context['cid_phone'] = get_thumbnail(static_path_get(u'img/ico-phone.png', '35x35'))
        context['cid_logo'] = u'/static/img/logo.png'
        context['cid_phone'] = u'/static/img/ico-phone.png'
        context['cid_time'] = u'/static/img/ico-time.png'

        items = []

        for item in context['order'].shoporderitem_set.select_related('product'):
            cid = get_thumbnail(item.product.productimage_set.all()[0].image, '90x90').url
            items.append({
                'title': item.product.title,
                'qty': item.qty,
                'sum': item.sum,
                'cid': cid
            })

        context['items'] = items

        return context


class ViewSitemapGen(MixinBase, TemplateView):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return HttpResponseNotFound()
        return super(ViewSitemapGen, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        from frontend.management.commands.site_map_gen import Command

        Command().execute()

        context = self.get_context_data(**kwargs)
        context['success'] = u'Карта успешно создана'

        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super(ViewSitemapGen, self).get_context_data(**kwargs)
        context['title'] = u'Генерация карты сайта'
        return context


class ViewYmlGen(MixinBase, TemplateView):
    template_name = 'frontend/view_sitemap_gen.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return HttpResponseNotFound()
        return super(ViewYmlGen, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        from frontend.management.commands.yml_gen import Command

        Command().execute()

        context = self.get_context_data(**kwargs)
        context['success'] = u'Yml успешно создан'

        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super(ViewYmlGen, self).get_context_data(**kwargs)
        context['title'] = u'Генерация Yml'
        return context


class ViewPriceSet(ViewSitemapGen):
    template_name = 'frontend/view_sitemap_gen.html'

    def post(self, request, *args, **kwargs):
        from frontend.management.commands.price_set import Command

        Command().execute()

        context = self.get_context_data(**kwargs)
        context['success'] = u'Подстройка цен успешно проведена'

        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super(ViewSitemapGen, self).get_context_data(**kwargs)
        context['title'] = u'Антиконкурент - подстройка цен'
        return context


class ViewTemplateToDb(ViewSitemapGen):
    template_name = 'frontend/view_sitemap_gen.html'

    def post(self, request, *args, **kwargs):
        from frontend.management.commands.template_to_db import Command

        Command().execute()

        context = self.get_context_data(**kwargs)
        context['success'] = u'Перенос шаблонов из файлов проведен'

        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super(ViewSitemapGen, self).get_context_data(**kwargs)
        context['title'] = u'Перенос шаблонов из файлов'
        return context


# def form_factory(qs, form_name='SpForm', prefix=''):
# fields = dict(
#     ('%s%s' % (prefix, cat_id), forms.BooleanField(label=title, initial=False))
#     for cat_id, title in qs.values_list('pk', 'title')
# )
#
# return type(form_name, (forms.Form,), fields)

class ViewPercentSet(MixinBase, FormView):
    # success_url = reverse_lazy('admin_super:frontend_product_changelist')
    def get_success_url(self):
        return reverse(
            'admin_super:frontend_productvariant_changelist') if self.cls_name == 'productvariant' else reverse(
            'admin_super:frontend_product_changelist')

    def get_form_class(self):
        class _Form(forms.Form):
            percent = forms.FloatField(label=_('percent'), initial=0)

        return _Form

    def form_valid(self, form):
        cd = form.cleaned_data
        dt = cd['percent'] / 100

        self.cls.objects.filter(pk__in=self.request.REQUEST['ids'].split(',')).update(
            price=F('price') + F('price') * dt)

        return redirect(self.get_success_url())
        # ct=%s&ids=%s

    def dispatch(self, request, *args, **kwargs):
        self.cls = ContentType.objects.get(pk=request.REQUEST['ct']).model_class()
        self.cls_name = self.cls.__name__.lower()

        return super(ViewPercentSet, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ViewPercentSet, self).get_context_data(**kwargs)
        context['product_num'] = len(self.request.REQUEST['ids'].split(','))
        context['success_url'] = self.get_success_url()

        return context


class ViewRegister(MixinBase, TemplateView):
    pass
