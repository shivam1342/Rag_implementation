# app.py
from flask import Flask, request, jsonify, render_template
from rag_core import rag_answer

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/rag", methods=["POST"])
def rag():
    data = request.json
    query = data.get("query")

    if not query:
        return jsonify({"error": "query is required"}), 400

    answer = rag_answer(query)
    return jsonify({"answer": answer})

if __name__ == "__main__":
    app.run(debug=True)
