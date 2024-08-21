mportant Links:
https://code.visualstudio.com/docs/python/tutorial-django
https://www.w3schools.com/django/
https://docs.djangoproject.com/en/5.0/
https://www.django-rest-framework.org
https://jsonlogic.com


Development Environment Guide:
1. Download latest version of Python from here:
https://www.python.org/downloads/.  

2. Create a FIZIT_DEV project directory on your computer

3. Create a virtual environment within that FIZIT_DEV (note the period before .venv)
python -m venv .venv 

4. Customize PYTHONPATH
Edit ./FIZIT_DEV/.venv/bin/activate
The file should look like this:

  # This file must be used with "source bin/activate" *from bash*

export PYTHONPATH=/Users/davidnichamoff/Projects/FIZIT_DEV/packages

deactivate () {
    # reset old environment variables
    if [ -n "${_OLD_VIRTUAL_PATH:-}" ] ; then
        PATH="${_OLD_VIRTUAL_PATH:-}"
        export PATH
        unset _OLD_VIRTUAL_PATH

5. Activate the virtual environment
source .venv/bin/activate

6. Install Django
pip install django
pip install -r requirements.txt

7. Create the project directory
cd FIZIT_DEV
django-admin startproject project .

8. Create the apps
cd FIZIT_DEV
python manage.py startapp api
python manage.py startapp frontend

You should now have the following directory structure:

FIZIT_DEV
FIZIT_DEV/project
FIZIT_DEV/api
FIZIT_DEV/frontend
FIZIT_DEV/.venv

9. Edit Settings File
Edit your FIZIT_DEV/project/settings.py file 
Make your settings look like mine, edit paths as appropriate

10. Clone the GIT FIZIT_DEV repository
git clone https://github.com/david-nichamoff/fizit-dev

11.  Apply initial migrations
python manage.py makemigrations
python manage.py migrate

12. Create superuser account
python manage.py createsuperuser

13. Start server to ensure everything installed
python manage.py runserver
visit your website at http://127.0.0.1:8000/

14. ./start.sh is a script to automatically start services
./stop.sh is a script to stop services






