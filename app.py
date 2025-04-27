import multiprocessing
from flask import Flask, render_template, redirect, url_for, session
from forms import TopicForm, QuizForm
from llm.quiz_logic import generate_questions, generate_answers, get_scores

app = Flask(__name__)
app.secret_key = 'super_secret'

def generate_answers_background(topic, questions, queue):
    '''Generate the answers under the hood while user solves the quiz'''
    # generate answers in the side process
    answers = generate_answers(topic, questions)
    # send the generated answers back into the main process
    queue.put(answers)


@app.route('/', methods=['GET', 'POST'])
def home():
    '''Home page where you have to type the topic'''
    topic_form = TopicForm()
    # whenever the topic is recieved, generate questions and redirect user to the quiz page
    if topic_form.validate_on_submit():
        # something is the default quiz topic
        session['topic'] = topic_form.topic.data.title() if topic_form.topic.data else "Something"
        # take the prepared questions and answer generation task (triggering it generates the answers)
        session['questions'] = generate_questions(session['topic'])
        # store the number of generated questions
        session['num_questions'] = len(session['questions'])

        # start generating the answers under the hood
        answers_queue = multiprocessing.Queue()
        answer_generation_process = multiprocessing.Process(target=generate_answers_background, args=(session['topic'], session['questions'], answers_queue))
        answer_generation_process.start()

        # Store the process and queue temporarily in the app context
        app.answers_queue = answers_queue
        app.answer_generation_process = answer_generation_process

        # redirect to the quiz page
        return redirect(url_for('quiz', topic=session['topic']))
    
    return render_template('home.html', form=topic_form, title='Welcome')


@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    '''Quiz page where questions are displayed dynamically'''
    # load the questions 
    questions=session['questions']
    quiz_form = QuizForm()
    # generate the answer fields if theyre not there yet (when the page just loads)
    if not quiz_form.answer_fields:
        for _ in range(session['num_questions']):
            quiz_form.answer_fields.append_entry()
    
    # whenever the answers are submitted
    if quiz_form.validate_on_submit():
        # collect the answers from each field (nested subform)
        session['user_answers'] = [answer_field.answer.data for answer_field in quiz_form.answer_fields]
        # wait for the answer generation process to end
        print("Waiting for answers...")
        answers_queue = app.answers_queue
        # get the answers when theyre ready
        answers = answers_queue.get() 
        # wait for the generation process to terminate (typically the same moment as when the answers are ready)
        app.answer_generation_process.join()
        session['answers'] = answers
        # compute the scores by passing the generated answers and user answers
        session['scores'] = get_scores(session['answers'], session['user_answers'])
        # redirect the user to results page with the scores
        return redirect(url_for('results'))

    # pair each question with corresponding answer field
    pairs = zip(questions, quiz_form.answer_fields)
    return render_template('quiz.html', form=quiz_form, pairs=pairs, title=f'{session.get('topic')} Quiz')

@app.route('/results')
def results():
    # zip all the quiz data
    quas = zip(session['questions'], session['user_answers'], session['answers'], session['scores'])
    total_score = sum(session['scores'])
    grade = round(100 * total_score / session['num_questions'], 1)
    return render_template('results.html', quiz_data=quas, total_score=total_score, grade=grade, title=f'{session['topic']} Quiz Results')


if __name__ == '__main__':
    app.run(debug=True)