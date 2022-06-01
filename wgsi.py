import config
from application import init_app


app = init_app()

if __name__ == "__main__":
    app.run(host=config.HOST, port=config.PORT)