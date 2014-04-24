from fabric.api import *
import os

PROJECTS_ROOT = os.path.split(os.path.abspath(os.path.dirname(__file__)))[0]

def deploy():
    #local('git add -A')

    #message = prompt("commit message: ")
    #local('git commit -m "%s"' % message)
    #local('git push origin master')

    env.host_string = 'xxx.xxx.xxx.xxx'
    env.user = 'xxx'
    env.key_filename = '%s/_deploy/flowershop/id_rsa' % PROJECTS_ROOT
    #env.password = ''
    with cd('/home/usr-alex/data/django-apps/vest'):
        run('git pull')

    code_dir = '/home/xxx/data/django-apps/flowershop/'
    with cd(code_dir):
        run('source /home/usr-alex/data/django15/bin/activate;cd /home/usr-alex/data/django-apps/flowershop; python manage.py migrate frontend')
        run('git pull')
        run('chmod -R 777 media')
        run('source /home/usr-alex/data/django15/bin/activate && python manage.py collectstatic --noinput ')
        run('touch reload')



deploy()