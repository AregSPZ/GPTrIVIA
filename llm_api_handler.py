import os
import json
import google.genai as genai
from google.genai.types import SafetySetting, HarmCategory, HarmBlockThreshold
from pydantic import BaseModel

class QA(BaseModel):
    '''Configure the model to provide Q&A in JSON format (for a simple retrieval of the data)'''
    # list of questions
    questions: list[str]
    # list of answers
    answers: list[str]

class SF(BaseModel):
    '''Configure the model to provide scores and feedback in JSON format'''
    # list of scores
    scores: list[str]
    # list of feedbacks
    feedback: list[str]

# load the Gemini API key
api_key = os.environ.get("GEMINI_API_KEY")

# activate api key
client = genai.Client(api_key=api_key)

def generate_qa(num_questions=10, difficulty="Gradual", topic="General"):
    """Generate Q&A pairs based on a particular topic"""

    topic = topic.title()

    # the prompt changes slightly for gradual and non gradual quizzes
    if difficulty == "Gradual":
        qa_prompt = f"Generate {num_questions} questions on the topic: {topic}. If the topic is very niche, admit that you don't have knowledge about it by writing '0' and nothing else. Gradually increase the difficulty of the questions, starting from the easiest ones and getting to hardest ones. Provide concise answers. List the questions first and then the answers at the end. Ensure the number of questions is exactly {num_questions}."
    else:
        difficulty_map = {"Easy": 2, "Moderate": 4, "Challenging": 6, "Very Difficult": 8, "Impossible": 10}
        difficulty_level = difficulty_map[difficulty]

        qa_prompt = f"Generate {num_questions} questions on the topic: {topic}. If the topic is very niche, admit that you don't have knowledge about it by writing '0' and nothing else. On a scale where 1 is the easiest and 10 is the hardest, each question should be of difficulty {difficulty_level}. Provide concise answers. List the questions first and then the answers at the end. Ensure the number of questions is exactly {num_questions}."

    # call the LLM
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[qa_prompt],
            config={
                'response_mime_type': 'application/json',
                'response_schema': list[QA],
                # strictly filter hate speech, harassment and sexual content
                "safety_settings": [
                    SafetySetting(
                    category=HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                    threshold=HarmBlockThreshold.BLOCK_LOW_AND_ABOVE
                    ),
                    
                    SafetySetting(
                        category=HarmCategory.HARM_CATEGORY_HARASSMENT,
                        threshold=HarmBlockThreshold.BLOCK_LOW_AND_ABOVE
                    ),

                    SafetySetting(
                        category=HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                        threshold=HarmBlockThreshold.BLOCK_LOW_AND_ABOVE
                    )
                ]
                }
            )
    # catch API service error
    except Exception as e:
        print(f"Caught Exception when trying to generate quiz:\n {e}")
        return (None, None, None)
    
    # the reponse is None if the topic was filtered
    if not response:
        return (None, None, None)
    
    # while the output is formatted like a json file, its still a string
    response_json = json.loads(response.text)[0]    
    questions, answers = response_json["questions"], response_json["answers"]
    # the numbers of actually generated questions 
    num_questions_actual = len(set(answers))
    print(questions, answers, '\n', num_questions_actual)

    # if 0 detected (topic is too niche to generate a meaningful quiz)
    if all(s == '0' for s in answers):
        return (None, None, None)
    
    # in case the model generates a fewer questions than user asked, adjust the quiz size accordingly (its better than generating nothing at all by sending an error)
    return questions, answers, num_questions_actual


def get_scores_with_feedback(QUAs):
    """Assign scores to user answers with personalized feedback"""
    # the base of the prompt
    scoring_prompt = f"You are provided with a series of question-correct answer-user answer triplets. Your task is to evaluate each user answer and assign it a score from 0 to 100, reflecting the accuracy, completeness, and relevance of the answer in relation to the correct answer. Also provide feedback for each user answer explaining what their answer lacks, as if you talk to the user directly. Provide the output in this way: all scores followed by all feedbacks. You don't have to repeat the user's answer at the start of the feedback.\n\n"

    # add the quiz data to the prompt
    for Q, U, A in QUAs:
        if not U.strip():
            U = "No answer was provided"
        qua = f"Question: {Q}\nCorrect Answer: {A}\nUser Answer: {U}\n\n"
        scoring_prompt += qua

    # invoke the LLM
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[scoring_prompt],
            config={
                'response_mime_type': 'application/json',
                'response_schema': list[SF]
                }
        )
    except Exception as e:
        print(f"Caught Exception when trying to generate scores and feedback: {e}")
        return (None, None)

    response_json = json.loads(response.text)[0]
    scores, feedback = response_json["scores"], response_json["feedback"]
    # normalize the scores
    for i in range(len(scores)):
        scores[i] = int(scores[i]) / 100
        if int(scores[i]) == scores[i]:
            scores[i] = int(scores[i])

    print(scores, feedback)
    return scores, feedback
