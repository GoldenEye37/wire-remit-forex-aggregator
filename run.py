# from flask_migrate import Migrate
# from app import create_app, db
from app import create_app

app = create_app()

cache = Cache(app)

request_middleware(app)

# migrate = Migrate(app, db)

if __name__ == '__main__':
    app.run(debug=True)

