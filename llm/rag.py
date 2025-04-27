import os
import requests
from langchain_community.llms import HuggingFacePipeline
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter as Splitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
from langgraph.graph import START, StateGraph
from typing_extensions import List, TypedDict

def fetch_squad():
    '''Fetch SQuAD.json from the internet'''
    dev_url = "https://rajpurkar.github.io/SQuAD-explorer/dataset/dev-v2.0.json"
    train_url = "https://rajpurkar.github.io/SQuAD-explorer/dataset/train-v2.0.json"
    
    print("Downloading SQuAD development set...")
    dev_response = requests.get(dev_url)
    dev_response.raise_for_status()
    dev_data = dev_response.json()

    print("Downloading SQuAD training set...")
    train_response = requests.get(train_url)
    train_response.raise_for_status()
    train_data = train_response.json()

    # Combine the data
    full_squad = {
        "data": dev_data["data"] + train_data["data"],
        "version": dev_data["version"]  # You might want to handle versioning more carefully
    }

    return full_squad

def get_quiz_answer(text):
    '''Extract the concise answer from the generated text'''
    # case 1: 
    # George Washington

    # President of the United States from March 4, 1789 until his death
    newline_split = text.split('\n', 1)
    if len(newline_split) > 1:
        return newline_split[0]
    
    # case 2: 
    # CPU stands for Central Processing Unit. It is a general purpose processor that runs programs written in
    sentence_split = text.split('.') if len(text.split('.')) > 1 else text.split(',')
    return sentence_split[0]


def generate_answer(qtopic, question, model_name="gpt2-xl",save_path="squad_faiss_index"):
    '''The following code implements Retrieval Augmented Generation (RAG) in its entirety: make a list of documents out of the dataset, make a vector store out of the documents, perform retrieval based on the prompt, generate the answer using the original question and retrieved context'''

    # load the LLM from hugging face hub
    llm = HuggingFacePipeline.from_model_id(
        model_id=model_name,
        task="text-generation",
        pipeline_kwargs={"max_new_tokens": 20, "temperature": 0.3, "top_k": 5, "top_p": 0.9, "repetition_penalty": 1.2}  
    )
    # Initialize embedding layer (will be used for initializing vector store)
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2", encode_kwargs={'normalize_embeddings': False})
    # Check if there's already a vector store saved
    if os.path.exists(save_path):
        print(f"Loading existing vector store from {save_path}")
        vector_store = FAISS.load_local(save_path, embeddings,allow_dangerous_deserialization=True)
    # if there none, create one (useful for speeding up the future quizzes)
    else:
        squad_data = fetch_squad()
        print("Making the documents out of json")
        documents = []
        # iterate through each entity
        for entity in squad_data["data"]:
            topic = entity["title"]
            # add all the context texts for the given entity
            for paragraph in entity["paragraphs"]:
                context = paragraph["context"]
                # Store raw context
                documents.append(Document(page_content=context, metadata={'topic': topic}))
        print("Splitting text")
        # split the documents into smaller chunks
        text_splitter = Splitter(chunk_size=175, chunk_overlap=20, add_start_index=True)
        docs = text_splitter.split_documents(documents)
        print("Initializing the vector store (performing the indexing)")
        vector_store = FAISS.from_documents(docs, embeddings)
        
        # Save the store to disk for future use
        vector_store.save_local(save_path)
        print(f"Vector store saved to {save_path}")

    # Make a prompt that will be used for the LLM that will answer to quiz questions
    prompt_template = """You are a quiz contestant aiming to achieve a high score. You will be given a question about {qtopic}, followed by relevant context. Provide the answer directly, without any additional explanation or sentences.

    Question:
    {question}

    Context:

    {context}

    Answer:"""

    rag_prompt = PromptTemplate.from_template(prompt_template)

    # define the application in a graph with LangGraph

    class State(TypedDict):
        # the input (question, start) is string, context (mid way) is list of LangGraph Documents, output is string (answer, end)
        qtopic: str
        question: str
        context: List[Document]
        answer: str

    # define application steps (retrieval and generation)
    def retrieve(state: State):
        # retrieve 4 documents as thats how much fits into gpt2-xl's context window + the prompt and generated answer
        retrieved_docs = vector_store.similarity_search(state['question'])
        # this node generates the context, so we return it
        return {"context": retrieved_docs}
    
    def generate(state: State):
        # merge the retrieved docs to pass it as one entity
        # explicitly mention which topic each context belongs to
        docs_content = "\n\n".join(doc.page_content for doc in state["context"])
        # invoke our prompt (generate the prompt by passing the parameters to the general template)
        prompt_text = rag_prompt.invoke({"qtopic": state["qtopic"], "question": state["question"], "context": docs_content})

        # pass the prompt to llm, generate the answer. # keep only the generated part
        answer = llm.invoke(prompt_text)[len(prompt_text.to_string()):].strip()

        return {"answer": answer}
    
    # compile and trigger the application
    graph_builder = StateGraph(State).add_sequence([retrieve, generate])
    graph_builder.add_edge(START, "retrieve")
    graph = graph_builder.compile()

    # finally, trigger the application with input topic and question
    print("Invoking the graph")
    response = graph.invoke({"qtopic": qtopic, "question": question})

    return get_quiz_answer(response["answer"])
