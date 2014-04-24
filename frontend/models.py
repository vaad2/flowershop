# -*- coding: utf-8 -*-
from common.fields import ExImageField
from common.models import AbstractTree, AbstractDefaultModel, AbstractSimplePage, AbstractMailTemplate_v_1_00, AbstractUserDefaultModel
from common.std import upload_def_get_2, upload_def_get, slugify_ru
import datetime
from common.thread_locals import get_current_request, get_current_user
from django.contrib.auth.models import User, AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

import logging

logger = logging.getLogger('flowershop.models')

# Create your models here.
class Category(AbstractTree):
    link = models.ForeignKey('self', blank=True, null=True, related_name='category_link')

    image = ExImageField(upload_to=upload_def_get('category_icon', field='self', name_gen=True), blank=True, null=True)
    #@property
    def url_get(self):
        if self.link:
            return self.link.url
        return self.url

    class Meta:
        verbose_name = _('category')
        verbose_name_plural = _('categories')
        ordering = ['site', 'inner_pos', 'pos', 'title']



class OrderStatus(AbstractDefaultModel):
    title = models.CharField(verbose_name=_('title'), max_length=255)

    def __unicode__(self):
        return self.title

    class Meta:
        verbose_name = _('order status')
        verbose_name_plural = _('orders status')
        ordering = ['-state', 'pos', 'title']


def default_order_status_get():
    try:
        return OrderStatus.active_objects.all()[0]
    except IndexError, e:
        return None


class Product(AbstractDefaultModel):
    category = models.ManyToManyField(Category, verbose_name=_('category'), blank=True, null=True)
    title = models.CharField(verbose_name=_('title'), max_length=255)

    art = models.CharField(verbose_name=_('art'), max_length=255, blank=True)

    consist = models.TextField(verbose_name=_('consists'), blank=True, null=True)
    weight = models.CharField(verbose_name=_('weight'), max_length=16, blank=True, null=True)
    size = models.CharField(verbose_name=_('size'), max_length=255, blank=True, null=True)

    price = models.FloatField(verbose_name=_('price'), default=0)
    price_old = models.FloatField(verbose_name=_('price old'), default=0)

    is_promo = models.BooleanField(verbose_name=_('is promo'), default=False)
    popular_cnt = models.PositiveIntegerField(verbose_name=_('popular cnt'), default=0)

    content = models.TextField(verbose_name=_('content'), blank=True, null=True)
    is_content_template = models.BooleanField(verbose_name=_('is content template'), default=False)

    slug = models.CharField(verbose_name=_('slug'), blank=True, null=True, db_index=True, max_length=255)

    product_related = models.ManyToManyField('self', verbose_name=_('product related'), blank=True, null=True)

    price_stop = models.FloatField(verbose_name=_('price stop'), default=10000)

    seo_title = models.CharField(verbose_name=_('seo title'), max_length=255, default='', blank=True)
    seo_keywords = models.CharField(verbose_name=_('seo keywords'), max_length=255, default='', blank=True)
    seo_description = models.CharField(verbose_name=_('seo description'), max_length=255, default='', blank=True)


    # percent = models.FloatField(verbose_name=_('percent'), default=0)

    def price_get(self):
        return self.price

    # price_get.short_description = _('current price')

    def url_get(self, cat=None):
        if not cat:
            cat = get_current_request().vt_category

        if not cat:
            try:
                cat = self.category.all()[0]
            except IndexError:
                logger.debug('product cat does not assign pk:%s' % self.pk)

        if cat:
            return mark_safe('%sproduct/%s/' % (cat.url_get(), self.slug))
        return 'javascript:void(0);'


    def product_images_get(self):
        return self.productimage_set.filter(state=True)

    def product_variants_get(self):
        return self.productvariant_set.filter(state=True)

    def product_related_get(self):
        qset = self.product_related.filter(state=True)

        ids_map = {}
        for product in qset:
            ids_map[product.pk] = product

        for img in ProductImage.active_objects.filter(product__in=ids_map.keys()).order_by('pos'):
            product = ids_map[img.product_id]
            if not hasattr(product, 'images'):
                product.images = []

            product.images.append(img)

        return qset

    def clean(self):
        if self.pk and len(self.slug) and Product.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
            raise ValidationError(_('product with same slug exists'))

    def __unicode__(self):
        return self.title

    def save(self, **kwargs):
        if not len(self.slug):
            self.slug = slugify_ru(self.title)

        super(Product, self).save(**kwargs)

    class Meta:
        verbose_name = _('product')
        verbose_name_plural = _('products')

class ProductVariant(AbstractDefaultModel):
    product = models.ForeignKey(Product, verbose_name=_('product'))
    title = models.CharField(verbose_name=_('title'), max_length=255)
    price = models.FloatField(verbose_name=_('price'), default=0)

    # percent = models.FloatField(verbose_name=_('percent'), default=0)

    def price_get(self):
        return self.price


    def __unicode__(self):
        return '%s - %s p.' % (self.title, self.price)

    class Meta:
        ordering = ['-state', 'pos', 'title']
        verbose_name = _('product variant')
        verbose_name_plural = _('product variants')


class ProductImage(AbstractDefaultModel):
    product = models.ForeignKey(Product)
    image = ExImageField(verbose_name=_('image'),
                         upload_to=upload_def_get_2('product/%s/%s', field='product', name_gen=True),
                         blank=True,
                         null=True)

    class Meta:
        verbose_name = _('product image')
        verbose_name_plural = _('product images')
        ordering = ['pos']





class Profile(AbstractDefaultModel):
    user = models.OneToOneField(User)
    phone = models.CharField(verbose_name=_('phone'), max_length=255, blank=True, null=True)

    class Meta:
        verbose_name = _('profile')
        verbose_name_plural = _('profiles')


class MailTemplate(AbstractMailTemplate_v_1_00):
    pass


class SimplePage(AbstractSimplePage):
    category = models.ManyToManyField(Category, verbose_name=_('category'), blank=True, null=True)

    # is_content_template = models.BooleanField(verbose_name = _('is content template'), default = False)


class News(AbstractUserDefaultModel):
    title = models.CharField(verbose_name=_('title'), max_length=255)
    date_time = models.DateTimeField(verbose_name=_('date time'), default=lambda: datetime.datetime.now())

    image = ExImageField(verbose_name=_('image'),
                         upload_to=upload_def_get('news', field='self', name_gen=True),
                         blank=True,
                         null=True)
    content_preview = models.TextField(verbose_name=_('content preview'), blank=True)
    content = models.TextField(verbose_name=_('content'))
    is_content_template = models.BooleanField(verbose_name=_('is content template'), default=False)

    slug = models.CharField(verbose_name=_('slug'), max_length=255, blank=True, null=True, db_index=True)

    def save(self, *args, **kwargs):
        if not len(self.content_preview):
            self.content_preview = strip_tags(self.content)[0:140]
        if not self.slug or not len(self.slug):
            self.slug = slugify_ru(self.title)

        super(News, self).save(*args, **kwargs)

    class Meta:
        verbose_name = _('news item')
        verbose_name_plural = _('news items')


class Slider(AbstractUserDefaultModel):
    slug = models.CharField(verbose_name=_('slug'), max_length=255, unique=True)
    title = models.CharField(verbose_name=_('title'), max_length=255, blank=True)

    class Meta:
        verbose_name = _('slider')
        verbose_name_plural = _('sliders')


class SliderImage(AbstractDefaultModel):
    slider = models.ForeignKey(Slider, verbose_name=_('slider'))
    url = models.CharField(verbose_name=_('url'), max_length=255, blank=True, null=True)
    image = ExImageField(verbose_name=_('image'),
                         upload_to=upload_def_get_2('slider_images/%s/%s', field='slider', name_gen=True),
                         blank=True,
                         null=True)


    class Meta:
        verbose_name = _('slider image')
        verbose_name_plural = _('slider images')


class UserProfile(models.Model):
    user = models.OneToOneField(User, verbose_name=_('user'))
    username = models.CharField(verbose_name=_('username'), max_length=255)
    phone = models.CharField(verbose_name=_('phone'), max_length=255)

    class Meta:
        verbose_name = _('user profile')
        verbose_name_plural = _('user profiles')


class FastOrder(AbstractDefaultModel):
    user = models.ForeignKey(User, verbose_name=_('user'), default=get_current_user, blank=True, null=True)
    phone = models.CharField(verbose_name=_('phone'), max_length=255)
    username = models.CharField(verbose_name=_('name'), max_length=255)
    product = models.ForeignKey(Product, verbose_name=_('product'))

    order_status = models.ForeignKey(OrderStatus, verbose_name=_('order status'), default=default_order_status_get,
                                     null=True)
    session_id = models.CharField(verbose_name=_('session'), db_index=True, blank=True, editable=False, max_length=255)

    class Meta:
        verbose_name = _('fast order')
        verbose_name_plural = _('fast orders')


class Settings(models.Model):
    name = models.CharField(verbose_name=_('name'), max_length=255)
    value = models.CharField(verbose_name=_('value'), max_length=255, blank=True)

    class Meta:
        verbose_name = _('settings')
        verbose_name_plural = _('settings')

    def save(self, **kwargs):
        if self.name == 'price_for_km':
            value = -1
            try:
                old_settings = Settings.objects.get(pk=self.pk, name='price_for_km')
                value = float(old_settings.value)

            except BaseException, e:
                logger.debug('cant find old settings %s' % e)

            if value != self.value:
                value = float(self.value)

                for city in City.objects.filter(is_fixed=False):
                    city.price = city.distance * value
                    city.save()

        super(Settings, self).save(**kwargs)


class City(AbstractDefaultModel):
    title = models.CharField(verbose_name=_('title'), max_length=255)
    region = models.CharField(verbose_name=_('region'), blank=True, max_length=255)
    distance = models.FloatField(verbose_name=_('distance'), default=0)
    price = models.FloatField(verbose_name=_('price'), default=0)
    is_fixed = models.BooleanField(verbose_name=_('is fixed'), default=False)

    def __unicode__(self):
        if self.region:
            return u'%s (%s)' % (self.title, self.region)
        return self.title

    class Meta:
        verbose_name = _('city')
        verbose_name_plural = _('cities')
        ordering = ['-state', 'pos', 'title']


class DeliveryType(AbstractDefaultModel):
    title = models.CharField(verbose_name=_('title'), max_length=255)
    price = models.FloatField(verbose_name=_('price'), default=0)

    def __unicode__(self):
        return self.title

    class Meta:
        verbose_name = _('delivery type')
        verbose_name_plural = _('delivery types')
        ordering = ['-state', 'pos', 'title']


class DeliveryTime(AbstractDefaultModel):
    title = models.CharField(verbose_name=_('title'), max_length=255)
    price = models.FloatField(verbose_name=_('price'), default=0)

    def __unicode__(self):
        return self.title

    class Meta:
        verbose_name = _('delivery time')
        verbose_name_plural = _('delivery time')
        ordering = ['-state', 'pos', 'title']


class PaymentType(AbstractDefaultModel):
    title = models.CharField(verbose_name=_('title'), max_length=255)
    description = models.TextField(verbose_name=_('description'), blank=True, null=True)
    price = models.FloatField(verbose_name=_('price'), default=0)

    def __unicode__(self):
        return self.title

    class Meta:
        verbose_name = _('payment type')
        verbose_name_plural = _('payment types')
        ordering = ['-state', 'pos', 'title']


class ShopOrder(AbstractDefaultModel):
    user = models.ForeignKey(User, blank=True, null=True)
    qty = models.PositiveIntegerField(verbose_name=_('qty'), default=0)
    sum = models.FloatField(verbose_name=_('sum'), default=0.0)
    delivery_sum = models.FloatField(verbose_name=_('delivery sum'), default=0.0)

    discount = models.FloatField(verbose_name=_('discount'), default=0.0)

    summary = models.FloatField(verbose_name=_('summary'), default=0.0)
    # delivery_item = models.ForeignKey(DeliveryItem, verbose_name=_('delivery item'))
    payment_type = models.ForeignKey(PaymentType, verbose_name=_('payment type'))

    #delivery
    city = models.ForeignKey(City, verbose_name=_('city'), blank=True, null=True)
    another_city = models.CharField(verbose_name=_('another city'), max_length=255, blank=True, null=True)

    distance = models.FloatField(verbose_name=_('km'), default=0)
    delivery_type = models.ForeignKey(DeliveryType, verbose_name=_('delivery type'))
    delivery_time = models.ForeignKey(DeliveryTime, verbose_name=_('delivery time'))

    #fields client
    client_name = models.CharField(verbose_name=_('client name'), max_length=255, blank=True, null=True)
    client_phone = models.CharField(verbose_name=_('client phone'), max_length=255)
    client_email = models.EmailField(verbose_name=_('client email'), max_length=255)
    client_comment = models.TextField(verbose_name=_('client comment'), blank=True, null=True)

    #fields receiver

    receiver_name = models.CharField(verbose_name=_('receiver name'), max_length=255, blank=True, null=True)
    receiver_address = models.TextField(verbose_name=_('receiver address'), max_length=255, blank=True, null=True)
    receiver_date_time = models.DateTimeField(verbose_name=_('receiver time'), max_length=255, blank=True, null=True)
    receiver_comment = models.TextField(verbose_name=_('receiver comment'), blank=True, null=True)

    session_id = models.CharField(verbose_name=_('session'), db_index=True, blank=True, editable=False, max_length=255)

    order_status = models.ForeignKey(OrderStatus, verbose_name=_('order status'), default=default_order_status_get,
                                     null=True)
    payment_status = models.BooleanField(verbose_name=_('payment status'), default=False)

    class Meta:
        verbose_name = _('shop order')
        verbose_name_plural = _('shop orders')

#
class ShopOrderItem(AbstractDefaultModel):
    shop_order = models.ForeignKey(ShopOrder, verbose_name=_('shop order'))
    product = models.ForeignKey(Product, verbose_name=_('product'))

    product_variant = models.ForeignKey(ProductVariant, verbose_name=_('product variant'), blank=True, null=True)

    qty = models.PositiveIntegerField(verbose_name=_('qty'), default=0)
    sum = models.FloatField(verbose_name=_('sum'), default=0.0)

    class Meta:
        verbose_name = _('shop order item')
        verbose_name_plural = _('shop order items')


class LinkedSite(AbstractDefaultModel):
    host = models.CharField(verbose_name=_('host'), max_length=255)

    def __unicode__(self):
        return self.host

    class Meta:
        verbose_name = _('linked site')
        verbose_name_plural = _('linked sites')


class LinkedPrice(AbstractDefaultModel):
    linked_site = models.ForeignKey(LinkedSite, verbose_name=_('linked site'))
    product = models.ForeignKey(Product, verbose_name=_('product'))
    url = models.CharField(verbose_name=_('url'), max_length=255)
    price = models.FloatField(default=0)

    class Meta:
        verbose_name = _('linked price')
        verbose_name_plural = _('linked prices')
        unique_together = [['linked_site', 'product']]


class Discount(AbstractDefaultModel):
    sum = models.FloatField(_('discount sum'))
    percent = models.FloatField(_('discount percent'))

    @classmethod
    def discount_get(cls, sum):
        qset = cls.active_objects.all()
        if not qset.count():
            return 0, 0, 0

        try:
            item = qset.filter(sum__lte=sum).order_by('-sum')[0]
            try:
                item_next = qset.filter(sum__gt=item.sum).order_by('sum')[0]
                next = item_next.sum - sum
                pc = item_next.percent
            except BaseException, e:
                next = 0
                pc = 0
            return item.percent, next, pc
        except IndexError, e:
            item = qset.order_by('sum')[0]
            return 0, item.sum - sum, item.percent

    class Meta:
        ordering = ['-state', 'sum']
        verbose_name = _('discount')
        verbose_name_plural = _('discounts')