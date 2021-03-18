import sentry_sdk
from ecosante import create_app
from sentry_sdk.integrations.flask import FlaskIntegration
import logging
import os

logging.basicConfig(level=logging.DEBUG)

if os.getenv('SENTRY_DSN'):
    sentry_sdk.init(
        dsn=os.getenv('SENTRY_DSN'),
        integrations=[FlaskIntegration()],
        traces_sample_rate=1.0
    )

app = create_app()

if __name__ == "__main__":
    app.run()