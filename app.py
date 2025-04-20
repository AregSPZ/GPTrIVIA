from flask import Flask, render_template, redirect, url_for, session
from forms import TopicForm, QuizForm
from transformers_pipeline import generate_qa, get_scores

app = Flask(__name__)
app.secret_key = 'super_secret'

@app.route('/', methods=['GET', 'POST'])
def home():
    '''Home page where you have to type the topic'''
    topic_form = TopicForm()
    # whenever the topic is recieved, generate questions and redirect user to the quiz page
    if topic_form.validate_on_submit():
        # something is the default quiz topic
        session['topic'] = topic_form.topic.data if topic_form.topic.data else "something"
        session['questions'], session['answers'] = generate_qa(session.get('topic'))
        # the number of generated (valid) questions can be determined by the number of generated answers
        session['num_questions'] = len(session['answers'])
        session['questions'] = session['questions'][:session['num_questions']]
        return redirect(url_for('quiz', topic=session['topic']))
    return render_template('home.html', form=topic_form, title='Welcome')


@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    '''Quiz page where questions are displayed dynamically'''
    # load the questions 
    questions=session.get('questions')
    quiz_form = QuizForm()
    # generate the answer fields if theyre not there yet (when the page just loads)
    if not quiz_form.answer_fields:
        for _ in range(session['num_questions']):
            quiz_form.answer_fields.append_entry()
    
    # whenever the answers are submitted
    if quiz_form.validate_on_submit():
        # collect the answers from each field (nested subform)
        user_answers = [answer_field.answer.data for answer_field in quiz_form.answer_fields]
        # pass the answers and compute the scores
        session['scores'] = get_scores(session['answers'], user_answers)
        return redirect(url_for('results'))

    # pair each question with corresponding answer field
    pairs = zip(questions, quiz_form.answer_fields)
    return render_template('quiz.html', form=quiz_form, pairs=pairs, title=f'{session.get('topic').title()} Quiz')

@app.route('/results', methods=['GET', 'POST'])
def results():
    return render_template('results.html', scores=session.get('scores'), title=f'{session['topic']} Quiz Results')


if __name__ == '__main__':
    app.run(debug=True)