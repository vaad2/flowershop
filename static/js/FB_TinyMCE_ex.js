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