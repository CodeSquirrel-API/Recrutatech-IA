from flask import Flask, jsonify, request

app = Flask(__name__)

def minha_funcao(payload):
    profissao = payload.get('profissao', '')
    conhecimento = payload.get('conhecimento', [])
    habilidade = payload.get('habilidade', [])
    atitude = payload.get('atitude', [])

    resultado = f"Profissão: {profissao}, Conhecimento: {conhecimento}, Habilidade: {habilidade}, Atitude: {atitude}"

    return resultado

@app.route('/colaborador', methods=['POST'])
def rota_principal():
    if request.method == 'POST' and request.is_json:
        payload = request.get_json()
        resultado = minha_funcao(payload)
        return jsonify({"resultado": resultado})
    else:
        return jsonify({"error": "Solicitação inválida"}), 400

if __name__ == '__main__':
    app.run(debug=True)
