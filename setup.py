from setuptools import find_packages, setup
from setuptools.command.install import install
from subprocess import call

DEPENDENCIES = [
    'celery',
    'email_validator',
    'Flask',
    'Flask-Assets',
    'Flask-Migrate',
    'Flask-SQLAlchemy',
    'Flask-WTF',
    'indice_pollution==0.3.4',
    'requests',
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
    extras_require={"dev": ["honcho"]},
    setup_requires=['pytest-runner'],
    tests_requires=['pytest'],
    cmdclass={
          'install': CustomPsycopg2Install,
    },
)
