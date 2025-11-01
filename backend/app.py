from flask import Flask
from flask_cors import CORS

# Importar blueprints
from auth.routes import bp as auth_bp
from reservas.routes import bp as reservas_bp
from sanciones.routes import bp as sanciones_bp

app = Flask(__name__)
CORS(app)

# Registrar blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(reservas_bp)
app.register_blueprint(sanciones_bp)

if __name__ == '__main__':
    app.run(debug=True)