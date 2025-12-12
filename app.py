from flask import Flask, render_template, jsonify, request
import requests
import datetime
import re
import random
import sqlite3



app = Flask(__name__)

# --- CONFIGURATION ---
DATABASE_NAME = 'celestium.db'
NASA_API_KEY = 'DPMUeB6R2Qk2hrsnl51R8Aa34BevwxJ3DwI3XEk4'  # Replace with your real key
NASA_URL = "https://api.nasa.gov/planetary/apod"

# --- AI ENGINE 1: TEXT ANALYZER ---
def ai_analyze_text(text):
    if not text: return {"summary": "No data.", "keywords": [], "time": "1 min read"}
    words = re.findall(r'\b[A-Z][a-z]{4,}\b', text)
    stopwords = {'There', 'Their', 'Where', 'Which', 'These', 'Image', 'Credit', 'Today', 'This', 'NASA', 'Space'}
    keywords = list(set([w for w in words if w not in stopwords]))[:3]
    summary = text.split('.')[0] + "."
    word_count = len(text.split())
    return {
        "summary": summary,
        "keywords": keywords,
        "time": f"{max(1, word_count // 200)} min read"
    }

# --- AI ENGINE 2: QUIZ GENERATOR (NLP) ---
def generate_quiz_from_text(text):
    questions = []
    sentences = text.split('. ')
    
    for sentence in sentences:
        number_match = re.search(r'\d+(?:,\d+)*(?:\.\d+)?(?:%|°C| km| million| billion| Ly| Billion Yrs)?', sentence)
        
        if number_match and len(questions) < 5:
            answer = number_match.group(0)
            question_text = sentence.replace(answer, "_______") + "?"
            
            options = [answer]
            try:
                val_str = re.findall(r'\d+', answer)[0].replace(',', '')
                val = float(val_str)
                suffix = "".join(re.findall(r'[^\d.,]+', answer))
                options.append(f"{int(val * 0.8)}{suffix}")
                options.append(f"{int(val * 1.2)}{suffix}")
                options.append(f"{int(val * 0.5)}{suffix}")
            except:
                options += ["Unknown", "0", "Infinite"]
            
            random.shuffle(options)
            correct_idx = options.index(answer)
            
            questions.append({
                "text": question_text,
                "options": options,
                "correct_answer": answer, 
                "explanation": f"Correct! The text states: '{sentence}.'"
            })

    if len(questions) < 3:
        keywords = list(set(re.findall(r'\b[A-Z][a-z]{5,}\b', text)))
        for word in keywords:
            if word not in ["There", "These", "Where", "Image", "NASA"]:
                sentence_with_word = next((s for s in sentences if word in s), None)
                if sentence_with_word:
                    q_text = sentence_with_word.replace(word, "_______") + "?"
                    options = [word, "Galaxy", "Nebula", "Orbit"]
                    random.shuffle(options)
                    correct_idx = options.index(word)
                    
                    questions.append({
                        "text": q_text,
                        "options": options,
                        "correct_answer": word,
                        "explanation": f"The term mentioned is {word}."
                    })

    return questions[:5]

# --- AI ENGINE 3: RECOMMENDATION ENGINE ---
@app.route('/api/get_recommendation')
def get_recommendation():
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    
    sequence = ["The Sun: Solar Engine", "Mercury", "Venus", "Earth", "Mars: The Red Planet", "Jupiter: King of Planets", "Saturn", "Uranus", "Neptune"]
    
    c.execute("SELECT topic, score, total_questions FROM quiz_results ORDER BY completed_at DESC LIMIT 1")
    last_result = c.fetchone()
    conn.close()

    if not last_result:
        return jsonify({
            "next_topic": sequence[0],
            "reason": "Welcome! Start your journey with the core of our system: The Sun."
        })

    topic, score, total = last_result
    mastery = (score / total) * 100
    current_index = sequence.index(topic) if topic in sequence else -1

    if mastery < 65:
        return jsonify({
            "next_topic": topic,
            "reason": f"Your score was {mastery:.0f}%. Let's re-read the lesson on {topic} for a deeper understanding."
        })
    
    elif mastery >= 85 and current_index < len(sequence) - 1:
        next_topic = sequence[current_index + 1]
        return jsonify({
            "next_topic": next_topic,
            "reason": f"Excellent! You mastered {topic}. Time to progress to {next_topic}."
        })
        
    else:
        return jsonify({
            "next_topic": "Mission Builder",
            "reason": "You've made great progress! Try a simulated mission for a practical challenge."
        })


# --- ROUTES (Page Navigation & Smart Routes) ---
@app.route('/')
@app.route('/index.html')
def home(): return render_template('index.html')
@app.route('/universe')
@app.route('/universe.html')
def universe(): return render_template('universe.html')
@app.route('/lessons')
@app.route('/lessons.html')
def lessons(): return render_template('lessons.html')
@app.route('/quizzes')
@app.route('/quizzes.html')
def quizzes(): return render_template('quizzes.html')
@app.route('/missions')
@app.route('/missions.html')
def missions(): return render_template('missions.html')
@app.route('/dashboard')
@app.route('/dashboard.html')
def dashboard(): return render_template('dashboard.html')


# --- API ENDPOINTS ---
@app.route('/api/feed')
def get_feed():
    try:
        print("\n---- FETCHING NASA FEED ----")

        today = datetime.date.today()
        start_date = today - datetime.timedelta(days=6)

        params = {
            "api_key": NASA_API_KEY,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": today.strftime("%Y-%m-%d")
        }

        response = requests.get(NASA_URL, params=params)

        print("NASA URL:", response.url)
        print("NASA Status:", response.status_code)

        if response.status_code != 200:
            return jsonify({"error": "NASA API error", "details": response.text}), 500

        data = response.json()

        print("NASA returned:", len(data), "items")

        processed_data = []

        # In case NASA returns a dict instead of a list:
        if isinstance(data, dict):
            data = [data]

        for item in reversed(data):  # latest first
            if item.get('media_type') != 'image':
                continue

            text = item.get('explanation', '')
            analysis = ai_analyze_text(text)

            processed_data.append({
                "title": item.get("title"),
                "date": item.get("date"),
                "image": item.get("url"),
                "original_text": text,
                "ai_summary": analysis["summary"],
                "ai_keywords": analysis["keywords"],
                "read_time": analysis["time"]
            })

        return jsonify(processed_data)

    except Exception as e:
        print("BACKEND ERROR:", e)
        return jsonify({"error": str(e)}), 500




@app.route('/api/generate_quiz', methods=['POST'])
def generate_quiz():
    try:
        data = request.json
        lesson_text = data.get('text', '')
        questions = generate_quiz_from_text(lesson_text)
        return jsonify(questions)
    except Exception as e:
        print(f"Quiz Error: {e}")
        return jsonify({"error": "Failed to generate quiz"}), 500

@app.route('/api/submit_quiz', methods=['POST'])
def submit_quiz():
    try:
        data = request.json
        topic = data.get('topic')
        score = data.get('score')
        total = data.get('total')
        
        if not all([topic, score is not None, total]):
            return jsonify({"error": "Missing quiz data"}), 400

        conn = sqlite3.connect(DATABASE_NAME)
        c = conn.cursor()
        c.execute(
            "INSERT INTO quiz_results (topic, score, total_questions) VALUES (?, ?, ?)",
            (topic, score, total)
        )
        conn.commit()
        conn.close()

        return jsonify({"message": "Quiz results saved successfully"}), 201

    except Exception as e:
        print(f"DB Submission Error: {e}")
        return jsonify({"error": "Failed to save results"}), 500

@app.route('/api/quiz_history')
def get_quiz_history():
    """FIXED: Fetches all past quiz results from the database."""
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    
    # Select all historical quiz data
    c.execute("SELECT topic, score, total_questions, completed_at FROM quiz_results ORDER BY completed_at DESC")
    history = c.fetchall()
    conn.close()

    # Convert the list of tuples into a list of dictionaries for JSON readability
    results = []
    for row in history:
        # Calculate mastery percentage
        mastery = (row[1] / row[2]) * 100
        
        results.append({
            "topic": row[0],
            "score": row[1],
            "total": row[2],
            "mastery": round(mastery, 1),
            "completed_at": row[3],
            "difficulty": "Advanced" if mastery > 80 else ("Intermediate" if mastery > 50 else "Beginner")
        })

    return jsonify(results)

@app.route('/api/simulate_mission', methods=['POST'])
def simulate_mission():
    commands = request.json.get('commands') 
    
    # Mars Map: 4x4 Grid
    # 1 = Rock Obstacle, 2 = Water Sample Target
    mars_map = [
        [0, 0, 1, 0], # Y=0 (Start Row)
        [0, 1, 0, 0], # Y=1 (Rock at X=1)
        [0, 0, 0, 2], # Y=2 (Target at X=3)
        [0, 0, 0, 0]  # Y=3 (Max Row)
    ]
    
    x, y = 0, 0 # Starting Position
    path_log = []
    final_status = "Incomplete"
    final_message = "Mission commands ended before reaching target."

    for cmd in commands:
        new_x, new_y = x, y
        move_message = ""
        
        # 1. Calculate the New Position
        if cmd == 'F': new_y += 1 
        elif cmd == 'R': new_x += 1 
        elif cmd == 'A': move_message = "Analyzed area."
        else: move_message = f"Ignored unknown command: {cmd}"

        # 2. Check for Boundaries and Obstacles before committing the move
        if cmd in ['F', 'R']:
            if not (0 <= new_x < 4 and 0 <= new_y < 4):
                final_status = "Failed"
                final_message = f"Rover drove off the map at ({new_x}, {new_y}) after command {cmd}!"
                path_log.append({'command': cmd, 'x': x, 'y': y, 'status': 'Off Map', 'message': final_message})
                break
            
            if mars_map[new_y][new_x] == 1:
                final_status = "Failed"
                final_message = f"Crashed into a rock at ({new_x}, {new_y}) after command {cmd}!"
                path_log.append({'command': cmd, 'x': x, 'y': y, 'status': 'Crashed', 'message': final_message})
                break
            
            # Commit the move
            x, y = new_x, new_y
            move_message = f"Moved to ({x}, {y})"
            
            # 3. Check for Target Hit after committing the move
            if mars_map[y][x] == 2:
                final_status = "Success"
                final_message = "Ancient water sample found! Mission Complete."
                path_log.append({'command': cmd, 'x': x, 'y': y, 'status': 'Goal', 'message': final_message})
                break
        
        # 4. Log the step (for analysis/display)
        path_log.append({'command': cmd, 'x': x, 'y': y, 'status': 'OK', 'message': move_message})

    # Return the full log and the final summary
    return jsonify({
        "status": final_status, 
        "message": final_message, 
        "path_log": path_log
    })


if __name__ == '__main__':
    print("------------------------------------------------")
    print(" Celestium Python Server Online")
    print(" URL: http://127.0.0.1:5000")
    print(" KEEP THIS WINDOW OPEN!")
    print("------------------------------------------------")
    app.run(debug=True, port=5000)