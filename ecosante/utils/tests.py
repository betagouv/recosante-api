from ecosante.recommandations.models import Recommandation

def published_recommandation(**kw):
    kw.setdefault('type_', 'generale')
    kw.setdefault('montrer_dans', ['newsletter'])
    kw.setdefault('status', 'published')
    return Recommandation(**kw)