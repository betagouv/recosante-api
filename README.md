# Recosante

 Un service public numérique de recommandations d'actions pour réduire l'impact de l'environnement sur sa santé. 

https://recosante.beta.gouv.fr/

## Brève description

Recosanté est composé de trois services :

 * Une API d’exposition des indicateurs qui est dans ce dépot, techniquement il s’agit d’une API écrite en python avec le framework Flask.
Cette API sert aussi à gérer les abonnements au service.

 * Un service qui envoie les newsletters, techniquement c’est un worker celery qui est passe toutes les heures pour voir s’il doit envoyer des mails ou bien des notifications web.

 * Un service qui sauvegarde les différents indices (indice ATMO, épisodes de pollution, Risque d'allergie lié à l'exposition aux pollens (RAEP), vigilance météo, indice UV). Le code de ce service se trouve [ici](github.com/betagouv/indice_pollution)

Les données sont stockées dans une base de données postgresql, dans le schéma public pour les données d’abonnements, et dans le schéma indice_schema pour les données de prévisions des différents indices renvoyés.


## Installation

### Vérification des variables d’environnement

Vous pouvez copier/coller le fichier .env.example vers un fichier .env ou bien .env.docker si vous souhaitez utiliser docker

Changez les variables `SECRET_KEY`, `AUTHENTICATOR_SECRET`, `JWT_SECRET_KEY`, `CAPABILITY_ADMIN_TOKEN` et `CAPABILITY_ADMIN_TOKEN` par une chaine de caractères générée de manière aléatoire.

Il faut aller chercher une clé d’API send in blue ici https://account.sendinblue.com/advanced/api, et la mettre dans la variable `SIB_APIKEY`


Vous devez aussi créer les clés pour envoyer des notifications à l’aide par exemple du service https://vapidkeys.com/

Ajoutez maintenant des adresses mails séparées par des espaces qui auront accès à l’interface d’administration dans la variable `ADMINS_LIST`.

### Avec Docker

En avant propos il faut avoir cloner dans le répertoire [indice_pollution](github.com/betagouv/indice_pollution) dans le répertoire parent de celui-ci ou bien changer son emplacement dans docker-compose dans services->indice_pollution->build->context.

Vous devez changer dans le fichier `.env.docker` les variables :
 * `SQLALCHEMY_DATABASE_URI`  par `postgresql://flask_celery:flask_celery@db/flask_celery`
 * `TEST_DATABASE_URL` par `postgresql://flask_celery:flask_celery@db/flask_celery_test`

Pour lancer les différents services vous pouvez utiliser [docker-compose](https://github.com/docker/compose), la première fois il faut lancer les migrations de `indice_pollution` avec `docker-compose up indice_pollution` une fois les migrations finies, vous pouvez lancer avec la commande `docker-compose up`, une fois tous les services lancés vous pouvez lancer un import de données avec `docker-compose exec indice_pollution python save_today.py` puis lancer les tests avec `docker-compose exec web pytest .`.

Vous pouvez ensuite accéder à l’API ici: (http://localhost:5000/v1/?insee=75056).

### Avec Linux

#### Dépendences système

 * Python 3.7+
 * Postgresql 12+
 * (Redis) peut être utilisé pour les tâches de fond

#### Service externe

Pour envoyer les mails il vout faut un compte https://sendinblue.com/

#### Création de la base de donnée

 * Il faut créer une base de données postgresql dédiée, avec par exemple : `create_db recosante`

#### Installation dépendences python

Après avoir cloné ce répertoire vous pouvez installer les dépendences avec `pip install .`

#### Initialisation de la base de données

Vous devez avant avoir installé la base de données de https://github.com/betagouv/indice_pollution/

Après avoir installé cette base de données, vous pouvez installer celle de ce dépôt avec `flask db upgrade`

## Démarrage

### Démarrage de l’API web

En développement vous pouvez démarrer l’API web avec `flask run`

### Démarrage des workers

Dans une autre fenêtre vous pouvez lancer les workers avec `celery --app ecosante.celery_worker.celery worker -E`
