

from flask import Flask, request, jsonify
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
import secrets, os,json
import logging
from functools import wraps
import sqlite3


logging.basicConfig(level=logging.INFO)  # Set the logging level to INFO

# Create a logger
logger = logging.getLogger(__name__)
#es_host = os.environ['ELASTICSEARCH_URL']
#print('Elastic host is {}'.format(es_host))
es = Elasticsearch(["http://elasticsearch:9200"])
# es = Elasticsearch([])
'''try:
 logger.info("--->%s", es.cat.indices())
except:
    pass
'''
app = Flask(__name__)
'''app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///authentication.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    

def __init__(self):
    conn = sqlite3.connect('authentication.db')
    print('database openend')
    cur=conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS keys (id INTEGER PRIMARY KEY AUTOINCREMENT,api_key VARCHAR(50) UNIQUE NOT NULL )" )
    conn.commit()
    print('table created')'''



def authenticate_key(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        api_key = request.headers.get('API-KEY')

        # Check if the API key exists in the database
        if api_key is None or not api_key_exists(api_key):
            return jsonify({"error": "Invalid API key"}), 401
        return func(*args, **kwargs)

    return wrapper

def api_key_exists(api_key):
    # Check if the provided API key exists in the database
    conn = sqlite3.connect('authentication.db')
    cur = conn.cursor()
    cur.execute("SELECT id FROM keys WHERE api_key = ?", (api_key,))
    result = cur.fetchone()
    return result is not None


@app.route('/generate_api_key', methods=['POST'])
def generate_api_key():
    try:
        # Generate a unique API key
        api_key = secrets.token_hex(16)

        # Store the API key in the SQLite database
        conn = sqlite3.connect('authentication.db')
        cur = conn.cursor()
        cur.execute("INSERT INTO keys (api_key) VALUES (?)",(api_key,))
        conn.commit()
        conn.close()

        return jsonify({"api_key": api_key}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route('/<index_name>/create', methods=['POST'])
@authenticate_key
def index_documents(index_name):
    try:
        index_exists = es.indices.exists(index=index_name)
        if not index_exists:
            data={"mappings":{
                "properties":{
                    "name":{"type":"text"},
                    "branch":{"type":"text"},
                    "city":{"type":"text"}
                }
            }}
            es.indices.create(index=index_name,body=data)
            
            #es.index(index=index_name,body=data)
        
        #dynamically making ES to not allow documents with different feilds
        mapping = es.indices.get_mapping(index=index_name)
        updated_map= mapping[index_name]
        updated_map['mappings']['dynamic']='strict' 
        es.indices.put_mapping(index=index_name, body=updated_map['mappings'])


        if 'file' in request.files:
            file = request.files['file']
            docs = json.load(file)

        else:
            raw_data = request.get_json()
            if raw_data is None:
                return jsonify({"error": "Invalid JSON data"}), 400
                
            docs = [raw_data]

        #manually making ES to not allow the documents with different feilds by checking the feilds
        '''bulk_data=[]
        failed=0
        success=0
        ind_count=es.count(index=index_name)
        mapping = es.indices.get_mapping(index=index_name)
        count= mapping[index_name]['mappings']
        for i in docs:
            if ind_count['count'] ==0:
                bulk_data.append({"_op_type": "index", "_index": index_name, "_source": i})
            else:
                
                if  set(mapping[index_name]["mappings"]["properties"].keys())==set(i.keys()):
                    bulk_data.append({"_op_type": "index", "_index": index_name, "_source": i})
                    success+=1


                else:
                    failed+=1
                    logger.error("feilds does not match")'''
    

        
        bulk_data = [
            {"_op_type": "index", "_index": index_name, "_source": doc}
            for  doc in docs]
    

        success,failed=bulk(es,bulk_data, index=index_name, raise_on_error=False)

        return jsonify({
            "success": success,
            "failed": failed
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
        


@app.route('/get_data/<index_name>', methods=['GET'])
@authenticate_key
def get_data(index_name):
    try:
        request_data = request.get_json()
      
        query = request_data.get('query')

        if  not query:
            result = es.search(index=index_name)
            hits = result.get('hits', {}).get('hits', [])
            documents = [hit['_source'] for hit in hits]
            
        else:

            result = es.search(index=index_name, body={"query": query})

            hits = result.get('hits', {}).get('hits', [])
            documents = [hit['_source'] for hit in hits]

        return jsonify(documents)
    except Exception as e:
        return jsonify({"error": f"Error retrieving data: {str(e)}"}), 500


@app.route('/update_data/<index_name>',methods=['POST'])
@authenticate_key
def update_data(index_name):
    try:
        request_data=request.get_json()

        Updated_data=es.update_by_query(index=index_name,body=request_data)
        
        return jsonify({'message':'document updated successfully'})
    except Exception as e:
        return jsonify({"error": f"Error updating data: {str(e)}"}), 500

@app.route('/delete_data/<index_name>',methods=['DELETE'])
@authenticate_key
def deleted_data(index_name):
    try:
        request_data=request.get_json()
        query=request_data.get('query')
        if  not query:
            return jsonify({"error": " 'query' parameters are required."}), 400
        deleted_data=es.delete_by_query(index=index_name,body={'query':query})
        return jsonify(deleted_data)
    except Exception as e:
        return jsonify({"error": f"Error deleting data: {str(e)}"}), 500




if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

