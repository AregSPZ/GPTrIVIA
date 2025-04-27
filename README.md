# GPTrIVIA - LLM Powered Quiz (GPT2-XL, LangChain, LangGraph, HuggingFace, FAISS, RAG, SQuAD, Flask, Docker)

## Overview
GPTrIVIA (Generative Pre Trained Transformer Trivia) is an interactive quiz platform powered by an advanced language model - GPT-2 XL, the largest model in GPT-2 family. The application gives you an opportunity to take a quiz on any topic of interest, which is made possible by cutting-edge technologies such as LangChain, LangGraph, and HuggingFace, ensuring an unforgettable experience. With FAISS and RAG integration, it ensures efficient retrieval of relevant information (from SQuAD dataset). The application is built with Flask for a seamless web interface and is fully containerized using Docker for easy deployment.
The FAISS vector database is pinned to the application to store and retrieve quiz-related data efficiently. This allows the application to provide quick responses to user queries, ensuring a smooth and engaging quiz experience.

## Features

- AI-powered quiz generation.
- Customizable question categories.
- Real-time scoring and feedback.
- Containerized with Docker.

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/AregSPZ/GPTrIVIA.git
    ```
2. Navigate to the project directory:
    ```bash
    cd GPTrIVIA
    ```
3. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1. Start the application:
    ```bash
    python app.py
    ```
2. Access the quiz interface at `http://localhost:5000`.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request.