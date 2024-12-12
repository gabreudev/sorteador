from flask import Flask, jsonify
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

app = Flask(__name__)
# Habilitando CORS para todas as rotas
CORS(app)

# Configurações do banco de dados
DB_CONFIG = {
    'dbname': os.getenv('DB_NAME', 'cores'),
    'user': os.getenv('DB_USER', 'admin'),
    'password': os.getenv('DB_PASSWORD', 'root'),
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432')
}

def get_db_connection():
    """Estabelece conexão com o banco de dados"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return None

@app.route('/random-data', methods=['GET'])
def get_random_data():
    """Busca uma cor e um nome aleatórios do banco de dados"""
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Erro ao conectar ao banco de dados'}), 500

        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Inicia a transação
            conn.autocommit = False
            
            # Busca uma cor aleatória
            cur.execute("SELECT cor FROM cores ORDER BY RANDOM() LIMIT 1")
            cor_result = cur.fetchone()
            
            # Busca um nome aleatório
            cur.execute("SELECT nome FROM nomes ORDER BY RANDOM() LIMIT 1")
            nome_result = cur.fetchone()

            if cor_result and nome_result:
                response = {
                    'cor': cor_result['cor'],
                    'nome': nome_result['nome']
                }
                
                # Usa parâmetros para evitar SQL injection
                cur.execute("DELETE FROM cores WHERE cor = %s", (cor_result['cor'],))
                cur.execute("DELETE FROM nomes WHERE nome = %s", (nome_result['nome'],))
                
                # Confirma as alterações
                conn.commit()
                
                return jsonify(response), 200
            else:
                # Reverte a transação se algo der errado
                conn.rollback()
                return jsonify({'error': 'Todos os nomes e cores já foram sorteados'}), 404

    except Exception as e:
        # Reverte a transação em caso de erro
        if conn:
            conn.rollback()
        return jsonify({'error': f'Erro ao buscar dados: {str(e)}'}), 500
    
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(debug=True)