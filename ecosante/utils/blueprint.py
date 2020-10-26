from flask import Blueprint as BaseBlueprint

class Blueprint(BaseBlueprint):
    def __init__(self, name, import_name, url_prefix=None):
        url_prefix = url_prefix or f'/{name}'
        return super().__init__(
            name,
            import_name,
            template_folder='templates',
            url_prefix=f'/{name}',
            static_folder='assets',
            static_url_path='/assets/'
        )