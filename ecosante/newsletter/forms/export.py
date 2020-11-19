from ecosante.utils.form import RadioField, BaseForm
from bs4 import BeautifulSoup
from wtforms import widgets
from flask import url_for
from markupsafe import Markup


class ListEditWidget(widgets.ListWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.secret_slug = None

    def __call__(self, field, **kwargs):
        html = super().__call__(field, **kwargs)
        soup = BeautifulSoup(html, 'html.parser')
        for l in soup.find_all('li'):
            id_ = l.input.attrs['value']
            link = soup.new_tag('a')
            link.attrs['href'] = url_for("recommandations.edit", id=id_)
            link.string = 'Éditer'
            l.label.insert_after(link)

        return Markup(soup)

class FormExport(BaseForm):
    recommandations = RadioField(
        'Choisir une recommandation préférée',
        choices=[],
        widget=ListEditWidget(prefix_label=False))