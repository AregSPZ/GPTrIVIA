from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SelectField, SubmitField, FieldList, FormField
from wtforms.validators import NumberRange

class QuizMakerForm(FlaskForm):
    '''The field for inserting the info about the structure of the quiz'''

    num_questions = IntegerField('Number of questions (3 to 100)', validators=[NumberRange(3, 100)]) 

    difficulty = SelectField('Choose difficulty', choices=[('Gradual', 'Gradual'), ('Easy', 'Easy'), ('Moderate', 'Moderate'), ('Challenging', 'Challenging'), ('Very Difficult', 'Very Difficult'), ('Impossible', 'Impossible')])

    topic = StringField('Type the topic here (Default: General)')

    submit_field = SubmitField('Submit')


class AnswerField(FlaskForm):
    '''The field for submitting an answer to a question'''
    class Meta:
        csrf = False  # Disable CSRF for nested forms (avoid overlap, its already handled by the parent form)
    answer = StringField('Your Answer')

# add difficulty and number of questions
class QuizForm(FlaskForm):
    '''The form of the quiz. It is dynamic and can take variable sizes to handle cases when the LLM generates a different number of questions than expected (5)'''
    # group answer fields (subforms) together to form the quiz form
    answer_fields = FieldList(FormField(AnswerField), min_entries=0)
    submit_field = SubmitField('Submit')