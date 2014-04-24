(function ($) {
    $.fn.center = function () {
        this.css('top', (($(window).height() - this.outerHeight()) / 2) + $(window).scrollTop() + 'px');
        this.css('left', (($(window).width() - this.outerWidth()) / 2) + $(window).scrollLeft() + 'px');
        return this;
    }

    $.fn.serializeObject = function (exdata) {
        var o = exdata || {};
        var a = this.serializeArray();
        $.each(a, function () {
            if (o[this.name]) {
                if (!o[this.name].push) {
                    o[this.name] = [o[this.name]];
                }
                o[this.name].push(this.value || '');
            } else {
                o[this.name] = this.value || '';
            }
        });
        return o;
    };



})(jQuery);


function basket_update(result) {
    if (result['success']) {
        $('.basket-qty').html(result['data']['qty']);
        $('.basket-sum-value').html(result['data']['sum']);
        if ('summary' in result['data']) $('.summary-value').html(result['data']['summary'][1]);
        if ('dsc_sum' in result['data']) {
            $('.basket-dsc-sum-value').html(result['data']['dsc_sum']);
            if (result['data']['dt_next']) {
                $('.dsc-block-next').show();
                $('.basket-pc-next').html(result['data']['pc_next']);
                $('.basket-dt-next').html(result['data']['dt_next']);
            }
            else {
                $('.dsc-block-next').hide();
            }

            if (result['data']['dsc']) {
                $('.dsc-block').show();
                $('.basket-dsc-pc').html(result['data']['pc_curr'])
                $('.basket-dsc').html(result['data']['dsc'])

            }
            else {
                $('.dsc-block').hide();

            }


//            if(result[''])
        }
    }
}

function post(url, data, handler) {
    jQuery.ajax({
        url: url,
        method: 'POST',
        data: data}).done(handler);
}

$(function () {
    var rtm = null;
    var cnt = $('.product-list-item').length;

    if (cnt) {
        function _refresh() {
            clearTimeout(rtm);

            var wd = $('body').width() - 270;
            var wdi = 220;//214
            var num = Math.floor(wd / wdi);

//            console.log(wd, wdi, num);
//            if (num > cnt) num = cnt;
            var dt = wd - num * 214;

            dt = Math.floor(dt / num / 2);

            rtm = setTimeout(function () {
                $('.product-list-item').css({margin: '10px ' + dt + 'px'});

            }, 500);

        }

        $(window).resize(_refresh);
        _refresh();

    }


    $('.search').val('');

    $('.search').autocomplete({
        serviceUrl: '/search/',
        minChars: 2,
        noCache: true,
        params: {cmd: 'search'},
        deferRequestBy: 500,
        onSelect: function (result) {
            document.location.assign(result['data']);

        }
    });


    $('.btn-basket').click(function () {
        var pk = $(this).data('pk');

        $.post('/cart/', {cmd: 'cart_add', pk: pk, pk_variant:$('.product-variant').val() }, function (result) {
            var jq_self = $('.popup-cart');
            jq_self.stop().css({opacity: 1.0}).hide()
            basket_update(result);

            jq_self.center().show().animate({opacity: 0}, 1500, function () {
                $(this).hide();
            });
        });
    });

    $('.popup-close').click(function () {
        $(this).closest('.popup').hide();
    })

    var jq_content_fo = $('.popup-fast-order-content');

    function fo_submit_handler() {
        post(g_urls['view_link']['frontend:ViewFastOrder'], jq_content_fo.find('form').serialize(), function (result) {
            if (result['data'] === true) {
                jq_content_fo.html('<div class="h1-title text-center">Спасибо</div><div class="text-center">В ближайшее время наш менеджер перезвонит вам</div>');
            }
            else {
                jq_content_fo.html(result['data']);
            }
        });
    }

    $('.btn-fast-order').click(function () {
        $.get(g_urls['view_link']['frontend:ViewFastOrder'], {product: $(this).data('pk')}, function (result) {
            console.log(result);
            if (result['success']) {
                jq_content_fo.html(result['data']).find('.btn-fast-order-submit').click(fo_submit_handler);
                $('.popup-fast-order').center().show();
            }
        })
    });


    $(".slides").cycle({
        fx: 'fade',
        speed: 400,
        timeout: 1400,
        pause: 0
    })
        .cycle('pause')
        .hover(
        function () {
            $(this).cycle('resume');
        },
        function () {
            $(this).cycle('pause');
        }
    );

})