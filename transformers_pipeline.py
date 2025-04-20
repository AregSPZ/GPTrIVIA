import re
from transformers import pipeline
from sentence_transformers import SentenceTransformer, util

def generate_qa(topic):
    """Generate 5 questions and answers based on a particular topic"""
    # Load the pipeline for text generation using the model name
    model_name = "gpt2-xl"
    qa_pipeline = pipeline("text-generation", model=model_name)
    topic = topic.lower()
    # a little prompt engineering
    prompt = f"List 5 concise school questions about {topic} with answers.\nQuestion 1: "
    
    # Generate text using the pipeline
    response = qa_pipeline(prompt, max_length=150, temperature=0.3, top_k=5, top_p=0.9, repetition_penalty=1.2, truncation=True, pad_token_id=50256)
    
    # Extract the generated text
    generated_text = response[0]["generated_text"]
    print(generated_text)
     # Use regex to extract question-answer pairs
    qa_pairs = re.findall(r"(Question \d+:.*?Answer:.*?)(?=Question \d+:|$)", generated_text, re.DOTALL)

    # Split the pairs into questions and answers
    questions = [re.search(r"Question \d+:(.*?)(?=Answer:)", pair, re.DOTALL).group(1).strip() for pair in qa_pairs]
    answers = [re.search(r"Answer:(.*)", pair, re.DOTALL).group(1).strip() for pair in qa_pairs]

    return questions, answers

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
            scores.append(cos_similarity)

    print(scores)
    return scores