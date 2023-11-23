# SeuArquivo.py

from flask import Flask, jsonify

app = Flask(__name__)

def minha_funcao():
    return "Olá do seu notebook!"

@app.route('/')
def rota_principal():
    resultado = minha_funcao()
    return jsonify({"resultado": resultado})

if __name__ == '__main__':
    app.run(debug=True)
