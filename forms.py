from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FieldList, FormField
from wtforms.validators import DataRequired

class TopicForm(FlaskForm):
    '''The field for inserting the topic of quiz'''
    topic = StringField('Type the topic here')
    submit_field = SubmitField('Submit')

class AnswerField(FlaskForm):
    '''The field for submitting an answer to a question'''
    class Meta:
        csrf = False  # Disable CSRF for nested forms (avoid overlap, its already handled by the parent form)
    answer = StringField('Your Answer', validators=[DataRequired()])

class QuizForm(FlaskForm):
    '''The form of the quiz. It is dynamic and can take variable sizes to handle cases when the LLM generates a different number of questions than expected (5)'''
    # group answer fields (subforms) together to form the quiz form
    answer_fields = FieldList(FormField(AnswerField), min_entries=0)
    submit_field = SubmitField('Submit')