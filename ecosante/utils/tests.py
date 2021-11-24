from ecosante.recommandations.models import Recommandation

def published_recommandation(**kw):
    kw.setdefault('type_', 'indice_atmo')
    kw.setdefault('status', 'published')
    return Recommandation(**kw)