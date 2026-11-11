import os
from flask import Flask, render_template
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from config import Config
from models import db, User

login_manager = LoginManager()
csrf = CSRFProtect()


def create_app():
    """Buat dan konfigurasi aplikasi Flask"""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Pastikan folder upload ada
    for folder in [Config.UPLOAD_FOLDER, Config.ENCRYPTED_FOLDER, Config.STEGO_FOLDER, Config.FACES_FOLDER]:
        os.makedirs(folder, exist_ok=True)

    # Inisialisasi ekstensi
    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Silakan login terlebih dahulu.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    from routes.auth import auth_bp
    from routes.messages import messages_bp
    from routes.files import files_bp
    from routes.stego import stego_bp
    from routes.blockchain import blockchain_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(messages_bp)
    app.register_blueprint(files_bp)
    app.register_blueprint(stego_bp)
    app.register_blueprint(blockchain_bp)

    # Dashboard route
    @app.route('/')
    def index():
        from crypto_utils import get_dongle_status
        return render_template('dashboard.html', dongle_status=get_dongle_status())

    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return render_template('base.html', error_code=404, error_message='Halaman tidak ditemukan'), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('base.html', error_code=500, error_message='Kesalahan server internal'), 500

    # Create tables
    with app.app_context():
        db.create_all()

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
