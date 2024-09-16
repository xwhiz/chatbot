from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema import StrOutputParser
from langchain.prompts import ChatPromptTemplate
from decouple import config


embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-mpnet-base-v2",
    model_kwargs={"device": "cuda"},
)

persist_directory = config("VECTOR_DOC_DB_PATH")

vectordb = Chroma(embedding_function=embeddings, persist_directory=persist_directory)

# llm from ollama
llm = ChatOllama(
    model="llama3.1",
)

# retriever
retriever = vectordb.as_retriever(search_method="cosine", top_k=3, threshold=0.5)


# Convert loaded documents into strings by concatenating their content
# and ignoring metadata
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


RAG_TEMPLATE = """
You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise.

<context>
{context}
</context>

Answer the following question:

{question}"""

rag_prompt = ChatPromptTemplate.from_template(RAG_TEMPLATE)

qa_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | rag_prompt
    | llm
    | StrOutputParser()
)


# # question = "Write snake game in python?"

# question = input("Enter your question: ")

# # result = qa_chain.invoke(question)
# # print(result)
# for chunk in qa_chain.stream(question):
#     print(chunk, end="", flush=True)
