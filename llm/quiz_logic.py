import re
from transformers import pipeline
from sentence_transformers import SentenceTransformer, util
from llm.rag import generate_answer

def generate_questions(topic):
    """Generate 5 questions based on a particular topic"""
    # generate the questions using vanilla gpt2-xl
    model_name = "gpt2-xl"
    qa_pipeline = pipeline("text-generation", model=model_name)
    topic = topic.lower()
    
    prompt = f"You're a quiz host. List 5 concise questions about {topic}.\n1. "
    
    # Generate questions
    response = qa_pipeline(prompt, max_length=100, temperature=0.3, top_k=5, top_p=0.9, repetition_penalty=1.2, truncation=True, pad_token_id=50256)
    
    # Extract the generated text
    generated_text = response[0]["generated_text"]

    # store the questions in a list
    questions = [q.strip()+"?" for q in re.findall(r'\d+\.\s(.*?)\?', generated_text)]
    
    return questions


def generate_answers(topic, questions):
    '''Generate the answers for the questions'''
    # generate answers for each question using GPT2-XL + RAG
    answers = []
    for question in questions:
        # pass the topic into question as well to assist in retrieving more relevant documents
        answers.append(generate_answer(topic, f"{topic}\n{question}"))

    return answers


def get_scores(answers, user_answers):
    '''Assign scores to user answers using a cosine similarity computed by a sentence transformer'''
    model = SentenceTransformer('all-MiniLM-L6-v2')
    scores = []
    # cosine similarity
    for i in range(len(answers)):
        # if the user hasnt provided an answer for a question
        if not user_answers[i]:
            scores.append(0)
        else:
            # compute embeddings
            embedding_true = model.encode(answers[i])
            embedding_user = model.encode(user_answers[i])
            # compute cosine similarity between embeddings
            cos_similarity = util.cos_sim(embedding_true, embedding_user)
            raw_score = cos_similarity[0].item()
            raw_score_rounded = round(raw_score, 2)
            scores.append(max(0, raw_score_rounded))

    return scores
