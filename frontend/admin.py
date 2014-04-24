import logging
from common.fields import AdminExImageFieldMixin
from common.models import FileJs, File, FileCss, FileImg, SiteTemplate, SiteTheme, SiteSettings
from common.std import ex_find_template
from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from sorl.thumbnail import get_thumbnail
from django.conf import settings
from frontend.models import *
# Delivery, DeliveryGroup, DeliveryItem
from django.utils.translation import ugettext_lazy as _

logger = logging.getLogger('flowershop.frontend.admin')

from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.contrib.auth.models import Group, User
from django.contrib.sites.models import Site


class InlineDefault(admin.TabularInline):
    extra = 0
    inline_classes = ('collapse open',)


class AdminImageDefault(admin.ModelAdmin):
    photo_set = None

    def _get_thumbnail(self, obj):
        try:
            image = getattr(obj, self.photo_set).all()[0]
            img_url = get_thumbnail('%s/%s' % (settings.PROJECT_ROOT, image.image.url), '140x140').url
            return u'<img src="%s" />' % img_url
        except BaseException, e:
            logger.error('bad thumbnail')

    _get_thumbnail.allow_tags = True
    _get_thumbnail.short_description = _('image')


class InlineProductImage(AdminExImageFieldMixin, InlineDefault):
    model = ProductImage


class AdminImageDefault(admin.ModelAdmin):
    photo_set = None

    def _get_thumbnail(self, obj):
        try:
            image = getattr(obj, self.photo_set).all().order_by('pos')[0]
            img_url = get_thumbnail('%s/%s' % (settings.PROJECT_ROOT, image.image.url), '140x140').url
            return u'<img src="%s" />' % img_url
        except BaseException, e:
            logger.error('bad thumbnail')

    _get_thumbnail.allow_tags = True
    _get_thumbnail.short_description = _('image')


class InlineLinkedPrice(admin.TabularInline):
    model = LinkedPrice
    extra = 0


class AdminLinkedSite(admin.ModelAdmin):
    list_display = ['id', 'host']
    list_editable = ['host']

    inlines = [InlineLinkedPrice]


class InlineProductVariant(admin.TabularInline):
    model = ProductVariant
    extra = 0


class AdminProduct(AdminImageDefault):
    photo_set = 'productimage_set'
    list_display = ['id', '_get_thumbnail', 'title', 'art', 'price', 'is_promo', 'popular_cnt', 'pos', 'state']
    list_editable = ['title', 'price', 'is_promo', 'popular_cnt', 'pos', 'state']
    exclude = ['consist', 'weight', 'size']

    save_as = True
    raw_id_fields = ['product_related', ]
    #related_lookup_fields = ['product_related']
    #
    related_lookup_fields = {
        'm2m': ['product_related'],
    }

    search_fields = ['title', 'content']
    inlines = [InlineProductVariant, InlineProductImage, InlineLinkedPrice]
    #

    actions = ['percent_set']



    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        if db_field.name == 'category':
            kwargs['queryset'] = Category.objects.get(pk=15).descendants_get()

        return super(AdminProduct, self).formfield_for_manytomany(db_field, request, **kwargs)

    def percent_set(self, request, queryset):
        selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
        ct = ContentType.objects.get_for_model(queryset.model)

        return redirect('%s?ct=%s&ids=%s' % (reverse('frontend:view_percent_set'), ct.pk, ",".join(selected)))
        # return HttpResponseRedirect("/export/?ct=%s&ids=%s" % (ct.pk, ",".join(selected)))

    percent_set.short_description = _('set percent')

    class Media:
        css = {
            'all': (
                '/static/codemirror/lib/codemirror.css',
                '/static/codemirror/codemirror_config.css'
            )
        }

        js = [
            '/static/grappelli/tinymce/jscripts/tiny_mce/tiny_mce.js',

            '/static/codemirror/lib/codemirror.js',
            '/static/codemirror/mode/xml/xml.js',
            '/static/codemirror/mode/jinja2/jinja2.js',
            '/static/codemirror/mode/javascript/javascript.js',
            '/static/codemirror/mode/css/css.js',
            '/static/codemirror/mode/htmlmixed/htmlmixed.js',

            '/static/codemirror/codemirror_tinymce.js', ]


class AdminCategory(AdminExImageFieldMixin, admin.ModelAdmin):
    def view_node(self, obj):
        style = 'font-size:%spx;' % (14 - obj.level)
        if obj.level == 1:
            style = '%sfont-weight:bold;' % style
        if not obj.level:
            return '<div style="white-space:nowrap;%sfont-weight:bold">%s %s</div>' % (
                style, '&nbsp;&nbsp;&nbsp;' * obj.level, obj.title)
        else:
            return '<div style="white-space:nowrap;%s">%s <span style="font-weight:bold">&nbsp;</span> %s</div>' % (
                style, '&nbsp;&nbsp;&nbsp;' * obj.level, obj.title)

    view_node.short_description = _('node view')
    view_node.allow_tags = True

    def _get_thumbnail(self, obj):
        try:

            # img_url = get_thumbnail('%s/%s' % (settings.PROJECT_ROOT, obj.image.url), '20x20').url
            return u'<img src="%s" style="background:orange;" />' % obj.image.url
        except BaseException, e:
            logger.error('bad thumbnail')

    _get_thumbnail.allow_tags = True
    _get_thumbnail.short_description = _('image')


    def _link_get(self, obj):
        if obj.link:
            url = reverse('admin_super:frontend_category_change', args=[obj.link.pk])
            return '<a href="%s">&raquo; %s:%s</a>' % (url, obj.link.pk, obj.link.title)
        return ''


    _link_get.allow_tags = True
    _link_get.short_description = _('link')

    list_display = ['id', '_get_thumbnail', 'view_node', 'title', 'url', '_link_get', 'pos', 'state']
    list_editable = ['title', 'url', 'pos', 'state']
    ordering = ['inner_pos']
    exclude = ['inner_pos', 'path', 'level', 'site', 'user']

    object = None

    def get_object(self, request, object_id):
        self.object = super(AdminCategory, self).get_object(request, object_id)
        return self.object

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if db_field.name == 'parent' and self.object:
            kwargs['queryset'] = Category.objects.exclude(path__istartswith=self.object.path)

        return super(AdminCategory, self).formfield_for_foreignkey(db_field, request, **kwargs)


class InlineShopOrderItem(InlineDefault):
    model = ShopOrderItem


class AdminShopOrder(admin.ModelAdmin):
    list_display = ['id', 'since', 'client_phone', 'client_email',
                    'order_status', 'summary', 'qty', 'payment_status']
    list_editable = ['order_status']

    inlines = [InlineShopOrderItem]


# class AdminSimplePage(admin.ModelAdmin):
#     list_display = ['id', 'site', 'title', 'url', 'seo_title', 'seo_keywords', 'seo_description', 'pos', 'state']
#     list_editable = ['site', 'title', 'url', 'pos', 'state']
#     exclude = ['user', 'site', 'nav_title', 'nav_show', 'is_content_template', 'extra_pos', 'position_nav',
#                'position_content']
#
#     list_filter = ['site']



class AdminNews(AdminExImageFieldMixin, admin.ModelAdmin):
    list_display = ['id', '_thumbnail_get', 'date_time', 'title', 'content_preview', 'state']
    list_editable = ['title', 'date_time', 'state']

    def _thumbnail_get(self, obj):
        try:
            image = obj.image
            img_url = get_thumbnail('%s/%s' % (settings.PROJECT_ROOT, image.url), '140x140').url
            return u'<img src="%s" />' % img_url
        except BaseException, e:
            logger.error('bad thumbnail')

    _thumbnail_get.allow_tags = True
    _thumbnail_get.short_description = _('image')

    class Media:
        css = {
            'all': (
                '/static/codemirror/lib/codemirror.css',
                '/static/codemirror/codemirror_config.css',
                '/static/css/custom_mce.css',
            )
        }

        js = [
            '/static/js/tinymce/tinymce.min.js',

            '/static/codemirror/lib/codemirror.js',
            '/static/codemirror/mode/xml/xml.js',
            '/static/codemirror/mode/jinja2/jinja2.js',
            '/static/codemirror/mode/javascript/javascript.js',
            '/static/codemirror/mode/css/css.js',
            '/static/codemirror/mode/htmlmixed/htmlmixed.js',

            '/static/js/custom_editor_setup.js', ]


class AdminSimplePage(admin.ModelAdmin):
    list_display = ['id', '_links_get', 'url', 'title', 'position_content', 'seo_title', 'seo_keywords',
                    'seo_description', 'pos', 'state']
    list_editable = ['url', 'title', 'position_content', 'pos', 'state']
    exclude = ['user', 'site', 'nav_title', 'nav_show', 'extra_pos', 'position_nav']

    def _links_get(self, obj):
        links = []
        for cat in obj.category.all().order_by('title'):
            links.append(
                '<a style="white-space:nowrap" target="_blank" href="%s"><b style="font-weight:bold">%s</b> %s</a>' % (
                    cat.url_get(), cat.title, cat.url_get()))

        return '<br/>'.join(links)

    _links_get.allow_tags = True
    _links_get.short_description = _('links')

    search_fields = ['title', 'content', 'seo_title', 'seo_description', 'seo_keywords', 'url']

    class Media:
        css = {
            'all': (
                '/static/codemirror/lib/codemirror.css',
                '/static/codemirror/codemirror_config.css',
                '/static/css/custom_mce.css',
            )
        }

        js = [
            '/static/js/tinymce/tinymce.min.js',

            '/static/codemirror/lib/codemirror.js',
            '/static/codemirror/mode/xml/xml.js',
            '/static/codemirror/mode/jinja2/jinja2.js',
            '/static/codemirror/mode/javascript/javascript.js',
            '/static/codemirror/mode/css/css.js',
            '/static/codemirror/mode/htmlmixed/htmlmixed.js',

            '/static/js/custom_editor_setup.js', ]


class AdminMailTemplate(admin.ModelAdmin):
    list_display = ['id', 'name', 'from_email', 'subject', 'recipients', 'template_html', 'template_text', 'state']
    list_editable = ['name', 'from_email', 'subject', 'recipients', 'template_html', 'template_text', 'state']
    exclude = ['user', 'site']
    save_as = True


class InlineSliderImage(AdminExImageFieldMixin, InlineDefault):
    model = SliderImage


class AdminSlider(AdminImageDefault):
    photo_set = 'sliderimage_set'

    inlines = [InlineSliderImage]
    exclude = ['user']

    list_display = ['id', '_get_thumbnail', 'slug', 'title']
    list_editable = ['slug', 'title']

    # user = models.ForeignKey(User, verbose_name=_('user'), default=get_current_user, blank=True, null=True)
    # phone = models.CharField(verbose_name=_('phone'), max_length=255)
    # username = models.CharField(verbose_name=_('name'), max_length=255)
    # product = models.ForeignKey(Product, verbose_name=_('product'))
    #
    # order_status = models.ForeignKey(OrderStatus, verbose_name=_('order status'), default=default_order_status_get)
    # session_id = models.CharField(verbose_name=_('session'), db_index=True, blank=True, editable=False, max_length=255)


class AdminFastOrder(admin.ModelAdmin):
    list_display = ['id', 'since', 'phone', 'username', 'order_status']
    list_editable = ['order_status']

#
# class InlineDeliveryGroup(admin.TabularInline):
#     model = DeliveryGroup
#     extra = 0
#
# class InlineDeliveryItem(admin.TabularInline):
#     model = DeliveryItem
#     extra = 0
#
#
# class AdminDeliveryGroup(admin.ModelAdmin):
#     list_display = ['id', 'delivery', 'title', 'pos', 'state']
#     list_editable = ['title', 'pos', 'state']
#     list_filter = ['delivery']
#     inlines = [InlineDeliveryItem]
#
# class AdminDelivery(admin.ModelAdmin):
#     list_display = ['id', 'title', 'pos', 'state']
#     list_editable = ['title', 'pos', 'state']
#     inlines = [InlineDeliveryGroup]
#


class InlineBase(admin.TabularInline):
    classes = ('grp-collapse grp-open',)
    exclude = ['user']
    inline_classes = ('grp-collapse grp-open',)


class InlineFile(InlineBase):
    model = File
    extra = 0


class InlineFileJs(InlineBase):
    model = FileJs
    extra = 0


class InlineFileCss(InlineBase):
    model = FileCss
    extra = 0


class InlineFileImg(InlineBase):
    model = FileImg
    extra = 0


class AdminSiteTemplate(admin.ModelAdmin):
    actions = ['recovery', 'reset_all', 'set_all']
    ordering = ['-state', 'name']

    def recovery(self, request, queryset):
        for item in queryset:
            item.content = ex_find_template(item.name, ['common.loaders.load_template_source'])[0]
            item.state = True
            item.save()

    recovery.short_description = _('recovery selected templates from files')

    def reset_all(self, request, queryset):
        queryset.update(state=False)

    reset_all.short_description = _('reset all')


    def set_all(self, request, queryset):
        queryset.update(state=True)

    set_all.short_description = _('set all')

    list_display = ['id', 'name', 'state']
    list_editable = ['name', 'state']
    exclude = ['site_theme']
    search_fields = ['content']
    inlines = [InlineFileCss, InlineFileJs, InlineFileImg, InlineFile]

    class Media:
        css = {
            'all': (
                '/static/codemirror/lib/codemirror.css',
                '/static/codemirror/codemirror_config.css',
            )
        }

        js = [

            '/static/codemirror/lib/codemirror.js',
            '/static/codemirror/mode/xml/xml.js',
            '/static/codemirror/mode/jinja2/jinja2.js',
            '/static/codemirror/mode/javascript/javascript.js',
            '/static/codemirror/mode/css/css.js',
            '/static/codemirror/mode/htmlmixed/htmlmixed.js',
            '/static/codemirror/codemirror_config.js'

            ]


class AdminProductVariant(admin.ModelAdmin):
    list_display=['id', 'product', 'title', 'price', 'pos', 'state']
    list_editable=['title', 'price', 'pos', 'state']

    actions = ['percent_set']
    def percent_set(self, request, queryset):
        selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
        ct = ContentType.objects.get_for_model(queryset.model)

        return redirect('%s?ct=%s&ids=%s' % (reverse('frontend:view_percent_set'), ct.pk, ",".join(selected)))
        # return HttpResponseRedirect("/export/?ct=%s&ids=%s" % (ct.pk, ",".join(selected)))

    percent_set.short_description = _('set percent')



def admin_register(admin_instance):
    admin_instance.register(Category, AdminCategory)
    admin_instance.register(Product, AdminProduct)
    admin_instance.register(ShopOrder, AdminShopOrder)
    admin_instance.register(SimplePage, AdminSimplePage)
    admin_instance.register(News, AdminNews)
    admin_instance.register(Slider, AdminSlider)
    admin_instance.register(City, list_display=['id', 'title', 'distance', 'price', 'is_fixed', 'pos', 'state'],
                            list_editable=['title', 'distance', 'price', 'is_fixed', 'pos', 'state'])
    admin_instance.register(DeliveryType, list_display=['id', 'title', 'price', 'pos', 'state'],
                            list_editable=['title', 'price', 'pos', 'state'])
    admin_instance.register(DeliveryTime, list_display=['id', 'title', 'price', 'pos', 'state'],
                            list_editable=['title', 'price', 'pos', 'state'])
    admin_instance.register(Settings, list_display=['id', 'name', 'value'], list_editable=['name', 'value'])

    admin_instance.register(PaymentType, list_display=['id', 'title', 'price', 'pos', 'state'],
                            list_editable=['title', 'price', 'pos', 'state'])
    admin_instance.register(OrderStatus, list_display=['id', 'title', 'pos', 'state'],
                            list_editable=['title', 'pos', 'state'])

    admin_instance.register(Discount, list_display=['id', 'sum', 'percent', 'state'], list_editable=[
        'sum', 'percent', 'state'
    ])

    admin_instance.register(FastOrder, AdminFastOrder)
    admin_instance.register(LinkedSite, AdminLinkedSite)

    admin_instance.register(SiteTemplate, AdminSiteTemplate)

    admin_instance.register(SiteSettings, list_display=['id', 'name', 'value', 'value_txt', 'description'],
                            list_editable=['name', 'value'])
    admin_instance.register(SiteTheme)

    admin_instance.register(User, UserAdmin)
    admin_instance.register(Group, GroupAdmin)
    admin_instance.register(Site, list_display=['id', 'domain', 'name'], list_editable=['domain', 'name'])

    admin_instance.register(ProductVariant, AdminProductVariant)

    # admin_instance.register(Delivery, AdminDelivery)
    # admin_instance.register(DeliveryGroup, AdminDeliveryGroup)