def template_to_source():
    import codecs
    apps_root = os.path.realpath('%s/../' % settings.PROJECT_ROOT)

    for st in SiteTemplate.objects.all():
        for filepath in loader.get_template_sources(st.name):
            try:
                if file_exists(filepath) and filepath.startswith(apps_root):
                    with codecs.open(filepath, 'w', 'utf8') as f:
                        f.write(st.content)
                        print st.name, filepath, '-ok'
            except IOError as e:
                pass