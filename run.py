from datetime import timedelta
from flask import Flask, render_template
from index import main


def create_app():
    app = Flask(__name__, template_folder='templates')

    @app.errorhandler(404)
    def not_found(_):
        return render_template('404.html'), 404

    @app.errorhandler(403)
    def not_found(_):
        return render_template('403.html'), 403

    app.secret_key = b'secret-key'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)

    app.register_blueprint(main)
    return app
