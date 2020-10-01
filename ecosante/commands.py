from flask import current_app
from flask_migrate import upgrade

@current_app.cli.command('startup')
def startup():
    upgrade()
    current_app.cli([
        'import-recommandations'
    ])