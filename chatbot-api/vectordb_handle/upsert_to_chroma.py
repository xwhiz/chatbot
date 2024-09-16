from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_huggingface import HuggingFaceEmbeddings
from decouple import config


def upload_pdf_to_chroma(pdf_path: str):
    loader = PyPDFLoader(pdf_path)
    texts = loader.load_and_split()

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-mpnet-base-v2",
        model_kwargs={"device": "cuda"},
    )

    persist_directory = config("VECTOR_DOC_DB_PATH")
    Chroma.from_documents(
        documents=texts, embedding=embeddings, persist_directory=persist_directory
    )
