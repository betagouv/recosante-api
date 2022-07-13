# Recosante

 Un service public numérique de recommandations d'actions pour réduire l'impact de l'environnement sur sa santé. 

https://recosante.beta.gouv.fr/


## Installation

### Dépendences système

 * Python 3.7+
 * Postgresql 12+
 * (Redis) peut être utilisé pour les tâches de fond

### Service externe

Pour envoyer les mails il vout faut un compte https://sendinblue.com/

### Création de la base de donnée

 * Il faut créer une base de données postgresql dédiée, avec par exemple : `create_db recosante`

### Installation dépendences python

Après avoir cloné ce répertoire vous pouvez installer les dépendences avec `pip install .`

### Initialisation de la base de données

Vous devez avant avoir installé la base de données de https://github.com/betagouv/indice_pollution/

Après avoir installé cette base de données, vous pouvez installer celle de ce dépôt avec `flask db upgrade`

## Démarrage

### Vérification des variables d’environnement


Vous pouvez copier/coller le fichier .env.example vers un fichier .env

Changez les variables `SECRET_KEY`, `AUTHENTICATOR_SECRET`, `JWT_SECRET_KEY`, `CAPABILITY_ADMIN_TOKEN` et `CAPABILITY_ADMIN_TOKEN` par une chaine de caractères générée de manière aléatoire.

Il faut aller chercher une clé d’API send in blue ici https://account.sendinblue.com/advanced/api, et la mettre dans la variable `SIB_APIKEY`


Vous devez aussi créer les clés pour envoyer des notifications à l’aide par exemple du service https://vapidkeys.com/


### Démarrage de l’API web

En développement vous pouvez démarrer l’API web avec `flask run`

### Démarrage des workers

Dans une autre fenêtre vous pouvez lancer les workers avec `celery --app ecosante.celery_worker.celery worker -E`
