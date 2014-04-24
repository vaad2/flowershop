# -*- coding: utf-8 -*-

from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from common.models import SiteTemplate

from grappelli.dashboard import modules, Dashboard
from grappelli.dashboard.utils import get_admin_site_name


class CustomIndexDashboard(Dashboard):
    """
    Custom index dashboard for www.
    """

    template = 'frontend/admin_dashboard.html'

    def init_with_context(self, context):
        site_name = get_admin_site_name(context)

        self.children.append(modules.ModelList(
            title=u'Оператору',
            column=1,
            models=(
                'frontend.models.ShopOrder',
                'frontend.models.FastOrder'
            )
        ))

        self.children.append(modules.ModelList(
            title=u'Контент-менеджеру',
            column=1,
            models=(
                'frontend.models.News',
                'frontend.models.SimplePage',
                'frontend.models.Product',
                'frontend.models.ProductVariant',

                'frontend.models.Slider',
                'frontend.models.Category',

            )
        ))

        self.children.append(modules.ModelList(
            title=u'Администратору',
            column=1,
            models=(
                'frontend.models.City',
                'frontend.models.Discount',
                'frontend.models.DeliveryType',
                'frontend.models.DeliveryTime',
                'frontend.models.PaymentType',
                'frontend.models.OrderStatus',
                'frontend.models.Settings',

                'frontend.models.LinkedSite',

                # 'django.contrib.auth.models.User',
                # 'frontend.models.UserProfile'
            )
        ))

        self.children.append(modules.ModelList(
            title=u'Программисту',
            column=1,
            models=(
                # 'frontend.models.MailTemplate',
                # 'vest.common.models.*',
                'common.models.SiteTemplate',
                'common.models.SiteSettings',
                'django.contrib.*'
            )
        ))

        if context['request'].user.is_superuser:
            self.children.append(modules.LinkList(
                u'Спец. функции',
                column=2,
                children=[
                    {
                        'title': u'Сформировать Yml',
                        'url': reverse('frontend:view_yml_gen'),
                        'external': False
                    },
                    {
                        'title': u'Сформировать Sitemap',
                        'url': reverse('frontend:view_sitemap_gen'),
                        'external': False
                    },
                    {
                        'title': u'Перенести шаблоны в базу',
                        'url': reverse('frontend:view_template_to_db'),
                        'external': False
                    },
                    {
                        'title': u'Запустить анти-конкурента',
                        'url': reverse('frontend:view_price_set'),
                        'external': False
                    },

                ]
            ))

        self.children.append(modules.LinkList(
            u'Инструкции',
            column=2,
            children=[
                {
                    'title': u'Работа с шаблонами',
                    'url': '/media/video/template.swf',
                    'external': False,
                },
                {
                    'title': u'Работа с простыми страницами',
                    'url': r'/media/video/simple_page.swf',
                    'external': False
                },
                {
                    'title': u'Добавление текста в шаблон',
                    'url': r'/media/video/add_text.swf',
                    'external': False
                },
                {
                    'title': u'Привязка нескольких страниц к одному url',
                    'url': r'/media/video/multiple_page.swf',
                    'external': False
                }
            ]
        ))

        # append a recent actions module
        self.children.append(modules.RecentActions(
            _('Recent Actions'),
            limit=5,
            collapsible=False,
            column=2,
        ))

        # # append a group for "Administration" & "Applications"
        # self.children.append(modules.Group(
        #     _('Group: Administration & Applications'),
        #     column=1,
        #     collapsible=True,
        #     children = [
        #         modules.AppList(
        #             _('Administration'),
        #             column=1,
        #             collapsible=False,
        #             models=('django.contrib.*',),
        #         ),
        #         modules.AppList(
        #             _('Applications'),
        #             column=1,
        #             css_classes=('collapse closed',),
        #             exclude=('django.contrib.*',),
        #         )
        #     ]
        # ))
        #
        # # append an app list module for "Applications"
        # self.children.append(modules.AppList(
        #     _('AppList: Applications'),
        #     collapsible=True,
        #     column=1,
        #     css_classes=('collapse closed',),
        #     exclude=('django.contrib.*',),
        # ))
        #
        # # append an app list module for "Administration"
        # self.children.append(modules.ModelList(
        #     _('ModelList: Administration'),
        #     column=1,
        #     collapsible=False,
        #     models=('django.contrib.*',),
        # ))


        # append a recent actions module
