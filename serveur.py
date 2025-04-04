from flask import Flask, request, jsonify
import requests
import json
from datetime import datetime, timedelta

app = Flask(__name__)

# Liste des dates déjà utilisées pour les publications
dates_occupees = [
    "2024-04-04", "2024-04-11", "2024-04-18", "2024-04-25"  # ← à actualiser dynamiquement + tard
]

def prochain_jeudi_libre(dates_occupees, date_forcee=None):
    if date_forcee:
        if date_forcee in dates_occupees:
            return None
        return date_forcee

    aujourd_hui = datetime.today().date()
    # Si on est vendredi ou après, on saute à la semaine prochaine
    if aujourd_hui.weekday() >= 4:
        aujourd_hui += timedelta(days=(7 - aujourd_hui.weekday()))
    else:
        aujourd_hui += timedelta(days=1)

    for i in range(1, 365):  # vérifie jusqu’à 1 an à l’avance
        jour = aujourd_hui + timedelta(days=i)
        if jour.weekday() == 3:  # 3 = jeudi
            jour_str = jour.strftime("%Y-%m-%d")
            if jour_str not in dates_occupees:
                return jour_str
    return None

@app.route('/publier-interview', methods=['POST'])
def publier():
    try:
        data = request.get_json(force=True)
        titre = data.get("titre")
        contenu_html = data.get("contenu_html")
        date_forcee = data.get("date_forcee")

        if not titre or not contenu_html:
            return jsonify({"error": "Champs manquants"}), 400

        date_publication = prochain_jeudi_libre(dates_occupees, date_forcee)

        if not date_publication:
            return jsonify({"error": "Pas de jeudi libre"}), 400

        article = {
            "title": titre,
            "content": contenu_html,
            "status": "draft",
            "categories": [5],  # ID de la catégorie "Interview"
            "date": f"{date_publication}T08:00:00"
        }

        # Remplacer ci-dessous par tes identifiants WP
        wp_url = "https://jouvenot.com/wp-json/wp/v2/posts"
        wp_user = "ton_login"
        wp_password = "ton_application_password"

        credentials = (wp_user, wp_password)
        headers = {"Content-Type": "application/json"}

        response = requests.post(wp_url, headers=headers, auth=credentials, data=json.dumps(article))

        if response.status_code == 201:
            return jsonify({"message": f"Brouillon programmé le {date_publication}"}), 201
        else:
            return jsonify({"error": "Échec WordPress", "details": response.text}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
