import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import datetime
from urllib.parse import quote

app = Flask(__name__)
CORS(app)

MONGO_URL = "mongodb+srv://akxon:ORPJo2mWWAtaJbjF@nova.dd9pdss.mongodb.net/?appName=nova"
mongo = MongoClient(MONGO_URL)
db = mongo["nova_ia"]
memoire_col = db["memoire"]
inconnu_col = db["inconnu"]

print("✅ Connecté à MongoDB Atlas !")

BASE = {
    "bonjour|salut|hello|hey|coucou|yo": "Salut ! 👋 Je suis NOVA ! Comment je peux t'aider ?",
    "qui es-tu|ton nom|tu es quoi|présente-toi": "Je suis NOVA, une IA auto-apprenante 🤖 Plus tu m'utilises, plus je deviens intelligente !",
    "blague|rigole|drôle|fais-moi rire": "Pourquoi les plongeurs plongent-ils en arrière ? 🤿 Parce que sinon ils tomberaient dans le bateau ! 😂",
    "merci|thanks|super|cool|génial": "Avec plaisir ! 😊",
    "au revoir|bye|ciao|à bientôt": "À bientôt ! 👋",
    "quelle heure": "dynamic_heure",
    "quelle date|quel jour": "dynamic_date",
    "comment tu fonctionnes|comment tu marches": "Je cherche dans ma mémoire MongoDB 🧠 Si je ne sais pas, j'ouvre Google et Wikipedia pour toi !",
}

def check_base(texte):
    lower = texte.lower()
    for mots, reponse in BASE.items():
        for mot in mots.split("|"):
            if mot in lower:
                return reponse
    return None

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    texte = data.get("texte", "").strip()
    lower = texte.lower()

    rep_base = check_base(texte)
    if rep_base:
        return jsonify({"reponse": rep_base, "source": "base"})

    toutes = list(memoire_col.find({}, {"_id": 0}))
    for entree in toutes:
        for mot in entree.get("mots", []):
            if mot.lower() in lower:
                return jsonify({"reponse": entree["reponse"], "source": "memoire"})

    inconnu_col.update_one(
        {"question": texte},
        {"$set": {"question": texte, "date": datetime.datetime.now()}, "$inc": {"count": 1}},
        upsert=True
    )

    query = quote(texte)
    google = f"https://www.google.com/search?q={query}"
    wiki = f"https://fr.wikipedia.org/wiki/Special:Search?search={query}"

    return jsonify({
        "reponse": "🔍 Je ne sais pas encore répondre à ça... Je cherche pour toi !",
        "source": "recherche",
        "google": google,
        "wiki": wiki
    })

@app.route("/memoire/ajouter", methods=["POST"])
def ajouter():
    data = request.json
    mots = data.get("mots", [])
    reponse = data.get("reponse", "")
    if not mots or not reponse:
        return jsonify({"erreur": "mots et reponse requis"}), 400
    memoire_col.insert_one({"mots": mots, "reponse": reponse, "date": datetime.datetime.now()})
    return jsonify({"ok": True})

@app.route("/memoire/liste", methods=["GET"])
def liste():
    toutes = list(memoire_col.find({}, {"_id": 0}))
    return jsonify({"memoire": toutes, "total": len(toutes)})

@app.route("/memoire/oublier", methods=["POST"])
def oublier():
    data = request.json
    mot = data.get("mot", "").lower()
    result = memoire_col.delete_many({"mots": mot})
    return jsonify({"ok": True, "supprimes": result.deleted_count})

@app.route("/", methods=["GET"])
def index():
    return jsonify({"status": "NOVA en ligne ✅"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Serveur NOVA démarré sur le port {port}")
    app.run(host="0.0.0.0", port=port)
