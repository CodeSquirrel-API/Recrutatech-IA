from flask import Flask, jsonify, request

app = Flask(__name__)

def minha_funcao(payload):

    name = payload.get('name', '')
    knowledge = payload.get('knowledge', '')
    skill = payload.get('skill', '')
    attitude = payload.get('attitude', '')
    experience = payload.get('experience', '')


    resultado = f"{name}! Conhecimento: {knowledge}, Habilidade: {skill}, Atitude: {attitude}, Experiência: {experience}"

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