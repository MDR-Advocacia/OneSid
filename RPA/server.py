from flask import Flask, request, jsonify
from flask_cors import CORS
import main # Importa nosso script principal do RPA

# Configura o servidor Flask
app = Flask(__name__)
# Habilita o CORS para permitir a comunicação com o React
CORS(app)

# Cria a nossa rota de API. O React vai enviar os dados para http://127.0.0.1:5000/run-rpa
@app.route('/run-rpa', methods=['POST'])
def run_rpa_endpoint():
    try:
        data = request.get_json()
        
        if not data or 'processos' not in data:
            return jsonify({"error": "A lista de 'processos' não foi encontrada."}), 400
            
        lista_processos = data['processos']
        print(f"API recebeu uma requisição para os processos: {lista_processos}")

        resultado = main.executar_rpa(lista_processos)

        print("RPA finalizado. Enviando resultado de volta para o front-end.")
        return jsonify(resultado)

    except Exception as e:
        print(f"Ocorreu um erro no servidor: {e}")
        return jsonify({"error": f"Ocorreu um erro interno no servidor: {e}"}), 500

if __name__ == '__main__':
    # host='0.0.0.0' permite que o React (e outras máquinas na rede) acesse o servidor
    app.run(host='0.0.0.0', port=5000, debug=True)