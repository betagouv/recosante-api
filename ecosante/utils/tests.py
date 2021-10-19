from ecosante.recommandations.models import Recommandation

def published_recommandation(**kw):
    kw.setdefault('type_', 'generale')
    kw.setdefault('medias', ['newsletter'])
    kw.setdefault('status', 'published')
    return Recommandation(**kw)