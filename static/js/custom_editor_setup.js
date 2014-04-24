var g_cm = {
    mode: 'text/html',
    tabMode: 'indent',
    lineNumbers: true,
    extraKeys: {
        "F11": function () {
            var scroller = editor.getScrollerElement();
            if (scroller.className.search(/\bCodeMirror-fullscreen\b/) === -1) {
                $('.CodeMirror').css({'maxWidth': 'none'});
                scroller.className += " CodeMirror-fullscreen";
                scroller.style.height = "100%";

                scroller.style.width = width + 'px';

                editor.refresh();


            } else {
                $('.CodeMirror').css({'maxWidth': '746px'});
                scroller.className = scroller.className.replace(" CodeMirror-fullscreen", "");
                scroller.style.height = '';
                scroller.style.width = '';
                editor.refresh();

            }
        },
        "Esc": function () {
            var scroller = editor.getScrollerElement();
            if (scroller.className.search(/\bCodeMirror-fullscreen\b/) !== -1) {
                $('.CodeMirror').css({'maxWidth': '746px'});
                scroller.className = scroller.className.replace(" CodeMirror-fullscreen", "");
                scroller.style.height = '';
                scroller.style.width = '';
                editor.refresh();
            }
        }
    }
};

function CustomFileBrowser(field_name, url, type, win) {
    tinymce.activeEditor.windowManager.open({
        title: "File browser",
        url: '/admin/filebrowser/browse/?pop=2&type=' + type,
        width: 800,
        height: 600
    }, {
        oninsert: function (url) {
            win.document.getElementById(field_name).value = url;
        }
    });
}

(function ($) {
    $(function () {
        console.log('code mirror tc init')
        tinymce.init({
//            selector: "textarea",
            file_browser_callback: CustomFileBrowser,
            theme: "modern",
            plugins: [
                "advlist autolink lists link image charmap print preview hr anchor pagebreak",
                "searchreplace wordcount visualblocks visualchars code fullscreen",
                "insertdatetime media nonbreaking save table contextmenu directionality",
                "emoticons template paste textcolor"
            ],
            toolbar1: "insertfile undo redo | styleselect | bold italic | alignleft aligncenter alignright alignjustify | bullist numlist outdent indent | link image",
            toolbar2: "print preview media | forecolor backcolor emoticons",
            image_advtab: true,
            templates: [
                {title: 'Test template 1', content: 'Test 1'},
                {title: 'Test template 2', content: 'Test 2'}
            ]
        });

        var id = 'id_content'; // ID of your textarea (no # symbol)
        var editor = null;

        function _init() {
//      var width = $('#id_content').parent().width();
            console.log('check')
            if ($('#id_is_content_template').attr('checked')) {
                console.log(1)
                tinyMCE.execCommand('mceRemoveEditor', false, id);
                editor = CodeMirror.fromTextArea(document.getElementById(id), g_cm);
            }
            else {
                console.log(2)
                if (editor) editor.toTextArea();
                tinyMCE.execCommand('mceAddEditor', false, id);

            }
        }

        $('#id_is_content_template').change(_init);

        _init();

    })

})(django.jQuery);


var FileBrowserDialogue = {
    init : function () {
        // remove tinymce stylesheet.
        var allLinks = document.getElementsByTagName("link");
        allLinks[allLinks.length-1].parentNode.removeChild(allLinks[allLinks.length-1]);
    },
    fileSubmit : function (FileURL) {
        top.tinymce.activeEditor.windowManager.getParams().oninsert(FileURL);
        tinyMCEPopup.close();
    }
}

if (typeof tinyMCEPopup.onInit !== 'undefined' )
    tinyMCEPopup.onInit.add(FileBrowserDialogue.init, FileBrowserDialogue);

