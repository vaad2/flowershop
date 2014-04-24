from django.conf.urls import patterns, include, url
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from views import *

urlpatterns = patterns('',
                       url(r'^$', csrf_exempt(ViewIndex.as_view()), name='view_index'),
                       url(r'^category/(?P<slug>[^\/]+)/$', ViewCategory.as_view(), name='view_index'),
                       url(r'^news/$', ViewNews.as_view(), name='view_news'),
                       url(r'^news/item/(?P<slug>[^\/]+)/$', ViewNewsItem.as_view(), name='view_news_item'),
                       url(r'^catalog/.+?/product/(?P<slug>[^/]+)/$', ViewProduct.as_view(), name='view_product'),
                       url(r'^catalog/.+?$', ViewProducts.as_view(), name='view_products'),
                       url(r'^cart/$', csrf_exempt(ViewCart.as_view()), name='view_cart'),
                       url(r'^search/$', ViewSearch.as_view(), name='view_search'),
                       url(r'^auth/$', ViewAuth.as_view(), name='view_auth'),
                       url(r'^cabinet/$', ViewCabinet.as_view(), name='view_cabinet'),
                       url(r'^logout/$', ViewLogout.as_view(), name='view_logout'),
                       url(r'^order/(?P<order_pk>[^/]+)/$', ViewOrder.as_view(), name='view_order'),
                       url(r'^confirm/(?P<pk>[^/]+)/$', ViewConfirm.as_view(), name='view_confirm'),
                       url(r'^robokassa/confirm/', ViewRobokassaConfirm.as_view(), name='view_robokassa_confirm'),
                       url(r'^robokassa/result/', ViewRobokassaResult.as_view(), name='view_robokassa_result'),
                       url(r'^robokassa/fail/', ViewRobokassaFail.as_view(), name='view_robokassa_fail'),

                       url(r'^admin/sitemap/gen/$', ViewSitemapGen.as_view(), name='view_sitemap_gen'),
                       url(r'^admin/yml/gen/$', ViewYmlGen.as_view(), name='view_yml_gen'),
                       url(r'^admin/template-to-db/$', ViewTemplateToDb.as_view(), name='view_template_to_db'),
                       url(r'^admin/price/set/$', ViewPriceSet.as_view(), name='view_price_set'),
                       url(r'^admin/percent/set/$', ViewPercentSet.as_view(), name='view_percent_set'),
                       # url(r'^email/test/(?P<pk>[^\/]+)/$', ViewTestEmail.as_view(), name='view_test_email'),




                       #catalog/rozy/product/zagolovok1/


)
