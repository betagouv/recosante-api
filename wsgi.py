from ecosante import create_app
import logging

logging.basicConfig(level=logging.DEBUG)

app = create_app()

if __name__ == "__main__":
    app.run()