from flask import Flask, jsonify, request
import pandas as pd
import psycopg2
from IPython.display import display
from sklearn.model_selection import cross_val_score
from sklearn.tree import DecisionTreeRegressor


app = Flask(__name__)

def getResultIa(cha):
    host = "silly.db.elephantsql.com"
    port = "5432"
    database = "ljppladj"
    user = "ljppladj"
    password = "JFgtpa3EjnB6zOJ75ejGn_gUOl8-dy3j"

    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )
        print("Conexão bem-sucedida!")
    except Exception as e:
        print(f"Erro ao conectar: {e}")

    cursor = conn.cursor()

    cursor.execute("""
    SELECT 
            candidates.cnd_id, 
            candidates.cnd_name, 
            candidates.cnd_email, 
            candidates.cnd_current_profession, 
            candidates.cnd_experience, 
            skl_skill.skl_name as skill,
            knw_knowledge.knw_name as knowledge,
            att_attitude.att_name as attitude
        FROM candidates
        LEFT JOIN candidate_skill ON candidates.cnd_id = candidate_skill.cnd_id
        LEFT JOIN skl_skill ON candidate_skill.knw_id = skl_skill.skl_id
        LEFT JOIN knw_knowledge ON skl_skill.skl_id = knw_knowledge.knw_id
        LEFT JOIN candidate_attitude ON candidates.cnd_id = candidate_attitude.cnd_id
        LEFT JOIN att_attitude ON candidate_attitude.knw_id = att_attitude.att_id

    """)

    df = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])

    df_skills = df[['cnd_id', 'cnd_name', 'cnd_email' ,'cnd_experience', 'skill']].drop_duplicates()
    df_knowledge = df[['cnd_id', 'cnd_name', 'cnd_experience', 'knowledge']].drop_duplicates()
    df_attitude = df[['cnd_id', 'cnd_name', 'cnd_experience', 'attitude']].drop_duplicates()

    cha = cha['desenvolvedor']
    habilidades = cha['habilidades']
    conhecimentos = cha['conhecimentos']
    atitudes = cha['atitudes']

    df_skills['tem_habilidade'] = 0
    df_knowledge['tem_conhecimento'] = 0
    df_attitude['tem_atitude'] = 0

    for habilidade in habilidades:
        df_skills['tem_habilidade'] = (df_skills['tem_habilidade'] | df_skills['skill'].fillna('').str.contains(habilidade, case=False)).astype(int)

    for conhecimento in conhecimentos:
        df_knowledge['tem_conhecimento'] = (df_knowledge['tem_conhecimento'] + 2 * df_knowledge['knowledge'].fillna('').str.contains(conhecimento, case=False)).astype(int)

    for atitude in atitudes:
        df_attitude['tem_atitude'] = (df_attitude['tem_atitude'] | df_attitude['attitude'].fillna('').str.contains(atitude, case=False)).astype(int)

    df_skills['num_habilidades'] = df_skills.groupby('cnd_id')['tem_habilidade'].transform('sum')
    df_attitude['num_atitudes'] = df_attitude.groupby('cnd_id')['tem_atitude'].transform('sum')
    df_knowledge['num_conhecimentos'] = df_knowledge.groupby('cnd_id')['tem_conhecimento'].transform('sum')

    df_final = df_skills.copy()

    df_final['pontos_cha'] = df_skills['num_habilidades'] + df_attitude['num_atitudes'] + df_knowledge['num_conhecimentos']

    df_final['num_atitudes'] = df_attitude['num_atitudes']
    df_final['num_conhecimentos'] = df_knowledge['num_conhecimentos']
    df_final = df_final.dropna(subset=['pontos_cha'])

    df_final = df_final.drop(['skill', 'cnd_experience'], axis=1)

    X = df_final[['cnd_id', 'tem_habilidade', 'num_habilidades',  'num_atitudes', 'num_conhecimentos']]
    y = df_final['pontos_cha']

    dt_regressor = DecisionTreeRegressor(random_state=42)

    scores = cross_val_score(dt_regressor, X, y, cv=5, scoring='neg_mean_squared_error')

    mse_scores = -scores

    average_mse = mse_scores.mean()

    dt_regressor.fit(X, y)

    X_novos = df_final[['cnd_id', 'tem_habilidade', 'num_habilidades', 'num_atitudes', 'num_conhecimentos']]

    previsoes = dt_regressor.predict(X_novos)

    resultados = pd.DataFrame({'pontuacao': previsoes})

    resultados = resultados.sort_values(by='pontuacao', ascending=False)

    colunas_para_remover = ['tem_habilidade', 'pontos_cha', 'num_habilidades', 'num_atitudes', 'num_conhecimentos']
    df_final = df_final.drop(colunas_para_remover, axis=1)

    df_final['pontuacao'] = previsoes

    df_final = df_final.sort_values(by='pontuacao', ascending=False)

    resultados = df_final

    pontuacao_minima = resultados['pontuacao'].min()
    pontuacao_maxima = resultados['pontuacao'].max()

    resultados['porcentagem'] = ((resultados['pontuacao'] - pontuacao_minima) / (pontuacao_maxima - pontuacao_minima)) * 100
    resultados['porcentagem'] = resultados['porcentagem'].astype(int)
    resultados = resultados.sort_values(by='porcentagem', ascending=False)
    resultados['texto_porcentagem'] = resultados['porcentagem'].map(qualificar_porcentagem)

    resultado = resultados.to_json(orient='records')
    resultado = [
            {"id": cnd_id, "name": cnd_name, "email": cnd_email, "pontuacao": pontuacao, "porcentagem": porcentagem, "qualificacao": texto_porcentagem}
            for cnd_id, cnd_name, cnd_email, pontuacao, porcentagem, texto_porcentagem in zip(resultados['cnd_id'], resultados['cnd_name'], resultados['cnd_email'], resultados['pontuacao'], resultados['porcentagem'], resultados['texto_porcentagem'])
    ]

    return resultado

def qualificar_porcentagem(x):
    if x < 50:
        return f'Menos qualificado: {x}%'
    elif x <= 70:
        return f'Qualificado: {x}%'
    else:
        return f'Altamente qualificado: {x}%'

def minha_funcao(payload):
    result = getResultIa(payload)
    return result

@app.route('/colaborador', methods=['POST'])
def rota_principal():
    if request.method == 'POST' and request.is_json:
        payload = request.get_json()
        resultado = minha_funcao(payload)
        return jsonify({"resultado": resultado})
    else:
        return jsonify({"error": "Solicitação inválida"}), 400
    

@app.route('/', methods=['GET'])
def hello_world():
        return ("Hello World")
  

if __name__ == '__main__':
    app.run(debug=True)
