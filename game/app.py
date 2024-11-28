from flask import Flask, render_template, request, session, redirect, url_for
import random
import nltk
import requests
from nltk.corpus import words

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # For session management

# Ensure the words dataset is downloaded
try:
    nltk.data.find('corpora/words.zip')
except LookupError:
    nltk.download('words')

# Load all dictionary words
word_list = words.words()

def fetch_word_meaning(word):
    """
    Fetch the meaning of the word using the Datamuse API.
    """
    try:
        response = requests.get(f"https://api.datamuse.com/words?sp={word}&md=d&max=1")
        if response.status_code == 200:
            data = response.json()
            if data and 'defs' in data[0]:
                meaning = data[0]['defs'][0].split('\t')[1]
                return meaning
        return "Meaning not available."
    except Exception as e:
        return f"Error fetching meaning: {e}"

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        # Get selected difficulty level
        difficulty = request.form['difficulty']
        if difficulty == 'easy':
            session['min_len'], session['max_len'], session['attempts'] = 4, 6, 10
        elif difficulty == 'medium':
            session['min_len'], session['max_len'], session['attempts'] = 6, 9, 8
        else:
            session['min_len'], session['max_len'], session['attempts'] = 9, 10, 6

        # Filter words based on difficulty
        valid_words = [
            word.lower() for word in word_list
            if session['min_len'] <= len(word) <= session['max_len']
        ]

        # Pick a random word
        session['word'] = random.choice(valid_words)
        session['meaning'] = fetch_word_meaning(session['word'])
        session['guesses'] = ''
        session['remaining_attempts'] = session['attempts']

        return redirect(url_for('game'))
    return render_template('home.html')

@app.route('/game', methods=['GET', 'POST'])
def game():
    word = session['word']
    guesses = session['guesses']
    remaining_attempts = session['remaining_attempts']
    meaning = session['meaning']

    if request.method == 'POST':
        guess = request.form['guess'].lower()
        if len(guess) == 1 and guess.isalpha():
            if guess not in guesses:
                session['guesses'] += guess
                if guess not in word:
                    session['remaining_attempts'] -= 1
        if session['remaining_attempts'] == 0:
            return render_template('game.html', word=word, guesses=guesses, 
                                   remaining_attempts=0, game_over=True, meaning=meaning)

    # Check if the word is guessed
    failed = any(char not in guesses for char in word)

    if not failed:
        return render_template('game.html', word=word, guesses=guesses, 
                               remaining_attempts=remaining_attempts, game_won=True, meaning=meaning)

    return render_template('game.html', word=word, guesses=guesses, 
                           remaining_attempts=remaining_attempts, meaning=meaning)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
