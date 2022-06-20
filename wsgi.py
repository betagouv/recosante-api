import sentry_sdk
from ecosante import create_app
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.redis import RedisIntegration
import logging
import os


logging.basicConfig(level=logging.DEBUG)

if os.getenv('SENTRY_DSN'):
    sentry_sdk.init(
        dsn=os.getenv('SENTRY_DSN'),
        integrations=[FlaskIntegration(), RedisIntegration()],
        traces_sample_rate=1.0
    )
    logging.getLogger(__name__).info('SENTRY SDK SET')


app = create_app()

if __name__ == "__main__":
    app.run()