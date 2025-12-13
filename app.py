from flask import Flask, render_template, jsonify, request
import requests
import datetime
import re
import random
import sqlite3
import os

app = Flask(__name__)

# -------------------------------------------------
# CONFIGURATION
# -------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_NAME = os.path.join(BASE_DIR, "celestium.db")

NASA_API_KEY = "DPMUeB6R2Qk2hrsnl51R8Aa34BevwxJ3DwI3XEk4"
NASA_URL = "https://api.nasa.gov/planetary/apod"


# -------------------------------------------------
# AI ENGINE 1: TEXT ANALYZER
# -------------------------------------------------
def ai_analyze_text(text):
    if not text:
        return {"summary": "No data.", "keywords": [], "time": "1 min read"}

    words = re.findall(r"\b[A-Z][a-z]{4,}\b", text)
    stopwords = {
        "There", "Their", "Where", "Which", "These",
        "Image", "Credit", "Today", "This", "NASA", "Space"
    }

    keywords = list(set([w for w in words if w not in stopwords]))[:3]
    summary = text.split(".")[0] + "."
    word_count = len(text.split())

    return {
        "summary": summary,
        "keywords": keywords,
        "time": f"{max(1, word_count // 200)} min read",
    }


# -------------------------------------------------
# AI ENGINE 2: QUIZ GENERATOR
# -------------------------------------------------
def generate_quiz_from_text(text):
    questions = []
    sentences = text.split(". ")

    for sentence in sentences:
        number_match = re.search(
            r"\d+(?:,\d+)*(?:\.\d+)?(?:%|°C| km| million| billion| Ly)?",
            sentence
        )

        if number_match and len(questions) < 5:
            answer = number_match.group(0)
            question_text = sentence.replace(answer, "_") + "?"

            options = [answer]
            try:
                val = float(re.findall(r"\d+", answer)[0])
                suffix = "".join(re.findall(r"[^\d.,]+", answer))
                options += [
                    f"{int(val * 0.8)}{suffix}",
                    f"{int(val * 1.2)}{suffix}",
                    f"{int(val * 0.5)}{suffix}",
                ]
            except Exception:
                options += ["Unknown", "0", "Infinite"]

            random.shuffle(options)

            questions.append({
                "text": question_text,
                "options": options,
                "correct_answer": answer,
                "explanation": f"The text states: '{sentence}.'"
            })

    return questions[:5]


# -------------------------------------------------
# RECOMMENDATION ENGINE (SAFE)
# -------------------------------------------------
@app.route("/api/get_recommendation")
def get_recommendation():
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        c = conn.cursor()

        c.execute("""
            SELECT topic, score, total_questions
            FROM quiz_results
            ORDER BY rowid DESC
            LIMIT 1
        """)

        last = c.fetchone()
        conn.close()

        sequence = [
            "The Sun: Solar Engine",
            "Mercury",
            "Venus",
            "Earth",
            "Mars: The Red Planet",
            "Jupiter: King of Planets",
            "Saturn",
            "Uranus",
            "Neptune"
        ]

        if not last:
            return jsonify({
                "next_topic": "LearnCore",
                "reason": "Continue exploring lessons to build your foundation."
            })

        topic, score, total = last
        mastery = (score / total) * 100
        idx = sequence.index(topic) if topic in sequence else -1

        if mastery < 65:
            return jsonify({
                "next_topic": topic,
                "reason": f"Your score was{mastery:.Of%}"
                f"Revisiting this lesson will help."
            })

        if mastery >= 85 and idx < len(sequence) - 1:
            return jsonify({
                "next_topic": sequence[idx + 1],
                "reason": "Excellent progress! Move to the next topic."
            })

        return jsonify({
            "next_topic": "Mission Builder",
            "reason": "You’re ready for a hands-on rover mission."
        })

    except Exception as e:
        print("RECOMMENDATION ERROR:", e)
        return jsonify({
            "next_topic": "LearnCore",
            "reason": "Continue learning while we prepare recommendations."
        })
# -------------------------------------------------
# PAGE ROUTES
# -------------------------------------------------


@app.route("/")
@app.route("/index")
def home():
    return render_template("index.html")


@app.route("/universe")
def universe():
    return render_template("universe.html")


@app.route("/lessons")
def lessons():
    return render_template("lessons.html")


@app.route("/quizzes")
def quizzes():
    return render_template("quizzes.html")


@app.route("/missions")
def missions():
    return render_template("missions.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


# -------------------------------------------------
# NASA FEED API
# -------------------------------------------------
@app.route("/api/feed")
def get_feed():
    try:
        today = datetime.date.today()
        start_date = today - datetime.timedelta(days=6)

        params = {
            "api_key": NASA_API_KEY,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": today.strftime("%Y-%m-%d"),
        }

        response = requests.get(NASA_URL, params=params)
        data = response.json()

        if isinstance(data, dict):
            data = [data]

        results = []

        for item in reversed(data):
            if item.get("media_type") != "image":
                continue

            analysis = ai_analyze_text(item.get("explanation", ""))

            results.append({
                "title": item.get("title"),
                "date": item.get("date"),
                "image": item.get("url"),
                "original_text": item.get("explanation", ""),
                "ai_summary": analysis["summary"],
                "ai_keywords": analysis["keywords"],
                "read_time": analysis["time"],
            })

        return jsonify(results)

    except Exception as e:
        print("NASA FEED ERROR:", e)
        return jsonify([])


# -------------------------------------------------
# QUIZ APIs
# -------------------------------------------------
@app.route("/api/generate_quiz", methods=["POST"])
def generate_quiz():
    try:
        text = request.json.get("text", "")
        return jsonify(generate_quiz_from_text(text))
    except Exception as e:
        print("QUIZ GEN ERROR:", e)
        return jsonify([])


@app.route("/api/submit_quiz", methods=["POST"])
def submit_quiz():
    try:
        data = request.json

        conn = sqlite3.connect(DATABASE_NAME)
        c = conn.cursor()
        c.execute(
            "INSERT INTO quiz_results (topic, score, total_questions) VALUES (?, ?, ?)",
            (data["topic"], data["score"], data["total"])
        )
        conn.commit()
        conn.close()

        return jsonify({"message": "Quiz saved"}), 201

    except Exception as e:
        print("QUIZ SAVE ERROR:", e)
        return jsonify({"error": "Quiz save failed"}), 500


@app.route("/api/quiz_history")
def quiz_history():
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()

    c.execute("""
        SELECT rowid, topic, score, total_questions
        FROM quiz_results
        ORDER BY rowid DESC
    """)

    rows = c.fetchall()
    conn.close()

    history = []
    for r in rows:
        mastery = (r[2] / r[3]) * 100
        history.append({
            "topic": r[1],
            "score": r[2],
            "total": r[3],
            "mastery": round(mastery, 1),
            "difficulty": (
                "Advanced" if mastery > 80 else
                "Intermediate" if mastery > 50 else
                "Beginner"
            )
        })

    return jsonify(history)


# -------------------------------------------------
# MISSION SIMULATOR
# -------------------------------------------------
@app.route("/api/simulate_mission", methods=["POST"])
def simulate_mission():
    try:
        data = request.get_json(force=True)
        commands = data.get("commands", [])
        if not isinstance(commands, list) or len(commands) == 0:
            return jsonify({
                "status": "Incomplete",
                "message": "No commands received.",
                "path_log": []
            })
        # Mars Map: 4x4 Grid
        # 1 = Rock, 2 = Target
        mars_map = [
            [0, 0, 1, 0],
            [0, 1, 0, 0],
            [0, 0, 0, 2],
            [0, 0, 0, 0],
        ]

        x, y = 0, 0
        path_log = []

        for cmd in commands:
            new_x, new_y = x, y
            message = ""

            if cmd == "F":
                new_y += 1
            elif cmd == "R":
                new_x += 1
            elif cmd == "A":
                message = "Analyzed area."
            else:
                message = f"Ignored command: {cmd}"

            if cmd in ["F", "R"]:
                if not (0 <= new_x < 4 and 0 <= new_y < 4):
                    return jsonify({
                        "status": "Failed",
                        "message": "Rover went off the map.",
                        "path_log": path_log
                    })

                if mars_map[new_y][new_x] == 1:
                    return jsonify({
                        "status": "Failed",
                        "message": "Rover crashed into rocks.",
                        "path_log": path_log
                    })

                x, y = new_x, new_y
                message = f"Moved to ({x}, {y})"

                if mars_map[y][x] == 2:
                    path_log.append({
                        "command": cmd,
                        "x": x,
                        "y": y,
                        "status": "Goal",
                        "message": "Water sample found!"
                    })

                    return jsonify({
                        "status": "Success",
                        "message": "Mission completed successfully.",
                        "path_log": path_log
                    })

            path_log.append({
                "command": cmd,
                "x": x,
                "y": y,
                "status": "OK",
                "message": message
            })

        return jsonify({
            "status": "Incomplete",
            "message": "Mission ended before reaching target.",
            "path_log": path_log
        })

    except Exception as e:
        print("MISSION ERROR:", e)
        return jsonify({
            "status": "Error",
            "message": "Mission simulation failed.",
            "path_log": []
        }), 500
# -------------------------------------------------
# SERVER START
# -------------------------------------------------


if __name__ == "__main__":
    print("------------------------------------------------")
    print(" Celestium Server Online")
    print(" http://127.0.0.1:5000")
    print("------------------------------------------------")
    app.run(debug=True, port=5000)
