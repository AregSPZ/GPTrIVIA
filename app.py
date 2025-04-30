import os
import tempfile
from flask import Flask, render_template, redirect, url_for, session
from flask_session import Session
from forms import QuizMakerForm, QuizForm
from llm_api_handler import generate_qa, get_scores_with_feedback

app = Flask(__name__)
# Sets up filesystem-based session storage (client side session fails to handle large data. this way we open the opportunity for large quizzes)
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = tempfile.gettempdir()
app.config["SESSION_PERMANENT"] = False
Session(app)
# get app's secret key
app.secret_key = os.environ.get("APP_SECRET_KEY")


@app.route('/', methods=['GET', 'POST'])
def home():
    '''Home page where you have to type the data about quiz structure'''

    quiz_maker = QuizMakerForm()

    # whenever the data is recieved, generate q&a and redirect user to the quiz page
    if quiz_maker.validate_on_submit():
        
        # store the quiz data
        session['num_questions'] = quiz_maker.num_questions.data if quiz_maker.num_questions.data else 10
        session['difficulty'] = quiz_maker.difficulty.data if quiz_maker.difficulty.data else "Gradual"
        session['topic'] = quiz_maker.topic.data.title() if quiz_maker.topic.data else "General"

        session['questions'], session['answers'], session['num_questions'] = generate_qa(num_questions=session['num_questions'], difficulty=session['difficulty'], topic=session['topic'])

        # catch the error during quiz generation
        if not session['questions']:
            return render_template("quiz_error.html", topic=session["topic"], title="Quiz Generation Error")
        
        # redirect to the quiz page
        return redirect(url_for('quiz', topic=session['topic']))
    
    return render_template('home.html', form=quiz_maker, title='Welcome')


@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    '''Quiz page where questions are displayed dynamically'''

    quiz_form = QuizForm()

    # generate the answer fields if theyre not there yet (when the page just loads)
    if not quiz_form.answer_fields:
        for _ in range(session['num_questions']):
            quiz_form.answer_fields.append_entry()
    
    # whenever the answers are submitted
    if quiz_form.validate_on_submit():
        # collect the answers from each field (nested subform)
        session['user_answers'] = [answer_field.answer.data for answer_field in quiz_form.answer_fields]
        
        # get the scores and feedback for the user
        session['scores'], session['feedback'] = get_scores_with_feedback(zip(session['questions'], session['user_answers'], session['answers']))

        # catch the error during score generation
        if not session['scores']:
            return render_template("results_error.html", title="Scores Generation Error")

        # redirect the user to results page with the scores and feedback
        return redirect(url_for('results'))

    # pair each question with corresponding answer field
    pairs = zip(session['questions'], quiz_form.answer_fields)
    return render_template('quiz.html', form=quiz_form, pairs=pairs, title=f'{session["topic"]} Quiz', difficulty=session['difficulty'])

@app.route('/results')
def results():
    # zip all the quiz data
    quasf = zip(session['questions'], session['user_answers'], session['answers'], session['scores'], session['feedback'])
    total_score = sum(session['scores'])
    grade = round(100 * total_score / session['num_questions'], 2)
    return render_template('results.html', quiz_data=quasf, total_score=total_score, grade=grade, title=f'{session['topic']}: Quiz Results')


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)