# -*- coding: utf-8 -*-
from sms.sms_ru import Client as SMSClient
from common.forms import decorator_placeholder
from common.views import MixinBase, AjaxView
import logging
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.db.models import Q
from django.forms import model_to_dict
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic import FormView, CreateView
from django import forms
from frontend.models import UserProfile, FastOrder, Product, Settings
from django.conf import settings

logger = logging.getLogger('flowershop.views')


class ViewIndex(AjaxView):
    def cmd_init(self, request):
        return 'ok'


class ViewAuth(AjaxView, FormView):
    def get_form_class(self):
        class _Form(forms.Form):
            email = forms.EmailField(label=_('E-mail'))
            password = forms.CharField(label=_('password'), widget=forms.PasswordInput)

            # @decorator_placeholder
            def __init__(self, *args, **kwargs):
                super(_Form, self).__init__(*args, **kwargs)

            def clean(self):
                cd = super(_Form, self).clean()

                user = authenticate(username=cd.get('email'), password=cd.get('password'))

                if not user:
                    raise forms.ValidationError(_('wrong password or email'))

                if not user.is_active:
                    raise forms.ValidationError(_('user not active'))

                self.user = user

                return cd

        return _Form


    def form_valid(self, form):
        login(self.request, form.user)
        return True


class ViewRegister(AjaxView, FormView):
    def get_form_class(self):
        class _Form(forms.Form):
            email = forms.EmailField(label=_('E-mail'))
            password = forms.CharField(label=_('password'), widget=forms.PasswordInput)
            password_repeat = forms.CharField(label=_('password repeat'), widget=forms.PasswordInput)
            username = forms.CharField(label=_('username'))
            phone = forms.CharField(label=_('phone'))

            # @decorator_placeholder
            def __init__(self, *args, **kwargs):
                super(_Form, self).__init__(*args, **kwargs)

            def clean(self):
                cd = super(_Form, self).clean()
                if cd.get('password') != cd.get('password_repeat'):
                    raise forms.ValidationError(_('passwords not same'))

                if User.objects.filter(email=cd.get('email')).exists():
                    raise forms.ValidationError(_('user with same email exist'))

                return cd


        return _Form


    def form_valid(self, form):
        cd = form.cleaned_data
        user = User.objects.create(email=cd['email'], username=cd['email'])
        UserProfile.objects.create(user=user, username=cd['username'], phone=cd['phone'])
        user.set_password(cd['password'])
        user.save()

        user = authenticate(username=cd['email'], password=cd['password'])
        login(self.request, user)

        return True


class ViewFastOrder(AjaxView, FormView):
    def get_form_class(self):
        class _Form(forms.Form):
            product = forms.CharField(widget=forms.HiddenInput, required=True)
            username = forms.CharField(label=_('username'), required=True)
            phone = forms.CharField(label=_('phone'), required=True)

            class Meta:
                model = FastOrder
                fields = ['username', 'product', 'phone']

            def clean_product(self):
                pk = self.cleaned_data['product']
                try:
                    Product.active_objects.get(pk=pk)
                except Product.DoesNotExist:
                    raise forms.ValidationError('product not found')
                return pk

            @decorator_placeholder
            def __init__(self, *args, **kwargs):
                super(_Form, self).__init__(*args, **kwargs)

        return _Form


    def get_initial(self):
        data = {'product': self.request.REQUEST['product']}
        user = self.request.user
        profile, user_pk = None, 0
        if user.is_authenticated():
            profile = user.userprofile
            user_pk = user.pk

        try:
            fo = FastOrder.active_objects.filter(Q(session_id=self.request.session.session_key)
                                                 | Q(pk=user_pk)).order_by('-pk')[0]
            dc = model_to_dict(fo, fields={'username': fo.username, 'phone': fo.phone})
            data.update(dc)

        except IndexError:
            if profile:
                data.update({'username': profile.username, 'phone': profile.phone})

        return data

    def form_valid(self, form):
        cd = form.cleaned_data
        FastOrder.active_objects.create(username=cd['username'], product_id=cd['product'], phone=cd['phone'],
                                        session_id=self.request.session.session_key)

        product = Product.active_objects.get(pk=cd['product'])

        sms_send(u'Быстрый заказ %s телефон %s, %s http://www.flowershop.ru%s' % (cd['username'], cd['phone'],
                                                                                 product.title, product.url_get()))
        return True


def sms_send(message):
    if getattr(settings, 'DISABLE_SMS_SEND', False):
        return
    try:
        phone = Settings.objects.get(name='sms_fast_order_phone').value
        key = Settings.objects.get(name='sms_api_id').value
        cl = SMSClient({'key': key})
        cl.send(phone, message=message)
    except BaseException, e:
        logger.error('sms send failed %s' % e)
