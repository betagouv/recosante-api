from setuptools import find_packages, setup
from setuptools.command.install import install
from subprocess import call

DEPENDENCIES = [
    'idna<3',
    'kombu==5.0.2',
    'amqp==5.0.1',
    'celery==5.0.3',
    'celery[redis]',
    'email_validator',
    'Flask',
    'Flask-Assets',
    'flask-cors',
    'Flask-Migrate',
    'Flask-SQLAlchemy',
    'Flask-WTF',
    'Flask-Manage-Webpack',
    'wtforms[email]',
    'indice_pollution==0.17.0',
    'sib-api-v3-sdk',
    'requests',
    'icalevents',
    'sentry-sdk[flask]',
    'redis'
]

class CustomPsycopg2Install(install):
    def run(self):
        install.run(self)
        call(['pip', 'install', '>=2.7', '--no-binary', 'psycopg2'])

setup(
    name='ecosante',
    version='0.1.0',
    description='ecosante.beta.gouv.fr',
    url='https://github.com/betagouv/ecosante',
    download_url='https://github.com/betagouv/ecosante/archive/0.1.0.tar.gz',
    author='Vincent Lara',
    author_email='vincent.lara@beta.gouv.fr',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3.8'
    ],
    keywords='air quality aasqa atmo iqa',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=DEPENDENCIES,
    extras_require={
        "dev": ["honcho", "watchdog"],
        "test": [
            'pytest',
            'pytest-alembic',
            'pytest-flask-sqlalchemy',
            'pytest-postgresql'
        ]
    },
    setup_requires=['pytest-runner'],
    test_suite='pytest',
    cmdclass={
          'install': CustomPsycopg2Install,
    },
)
