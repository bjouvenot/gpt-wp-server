from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import requests
import json

# === CONFIGURATION ===
wp_url_posts = "https://www.jouvenot.com/wp-json/wp/v2/posts"
wp_url_categories = "https://www.jouvenot.com/wp-json/wp/v2/categories"
wp_user = "Bertrand Jouvenot"
wp_app_password = "j4ZF PRKg NqCa 4ifO PiEA 0PiU"  # ⚠️ Identifiants toujours à garder secrets

app = Flask(__name__)

def get_next_available_thursday():
    now = datetime.now()
    for i in range(1, 15):
        test_day = now + timedelta(days=i)
        if test_day.weekday() == 3:  # jeudi
            date_str = test_day.strftime('%Y-%m-%d')
            r = requests.get(wp_url_posts, auth=(wp_user, wp_app_password), params={"status": "future"})
            if r.status_code == 200:
                for post in r.json():
                    if post.get("date", "").startswith(date_str):
                        break
                else:
                    return test_day.replace(hour=8, minute=0, second=0, microsecond=0).isoformat()
    return None

def get_category_id(name="Interview"):
    r = requests.get(wp_url_categories, auth=(wp_user, wp_app_password))
    if r.status_code == 200:
        for cat in r.json():
            if cat["name"].lower() == name.lower():
                return cat["id"]
    return None

@app.route('/publier-interview', methods=['POST'])
def publier():
    try:
        data = request.get_json(force=True)
        titre = data.get("titre")
        contenu = data.get("contenu_html")

        if not titre or not contenu:
            return jsonify({"error": "titre ou contenu_html manquant"}), 400

        date_publi = get_next_available_thursday()
        if not date_publi:
            return jsonify({"error": "Pas de jeudi libre"}), 400

        cat_id = get_category_id()
        if not cat_id:
            return jsonify({"error": "Catégorie 'Interview' non trouvée"}), 400

        payload = {
            "title": titre,
            "content": contenu,
            "status": "draft",
            "date": date_publi,
            "categories": [cat_id]
        }

        headers = {"Content-Type": "application/json"}
        r = requests.post(wp_url_posts, auth=(wp_user, wp_app_password), headers=headers, data=json.dumps(payload))

        if r.status_code in [200, 201]:
            return jsonify({"success": True, "url": r.json().get("link")})
        else:
            return jsonify({"error": r.text}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
