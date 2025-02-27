from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_qdrant import QdrantVectorStore
from tqdm import tqdm


# def upsert_pdf_to_qdrant(
#     vector_store: QdrantVectorStore, pdf_path: str, document_id: str
# ):
#     print("Creating loader")
#     loader = PyPDFLoader(pdf_path)

#     print("Loading and splitting")
#     documents = loader.load()

#     text_splitter = RecursiveCharacterTextSplitter(
#         chunk_size=1000, chunk_overlap=0, length_function=len, is_separator_regex=False,
#     )
#     texts = text_splitter.split_documents(documents)

#     # Create a progress bar
#     progress_bar = tqdm(total=len(texts), desc="Uploading documents", unit="doc")

#     # Add metadata to each document chunk before uploading
#     for i in range(0, len(texts), 4):
#         batch = texts[i : i + 4]

#         # Add document_id to metadata for each chunk
#         for text in batch:
#             if not text.metadata:
#                 text.metadata = {}
#             text.metadata["document_id"] = document_id  # Assign document_id
#             text.metadata["source"] = pdf_path  # Track the source file

#         vector_store.add_documents(batch)
#         progress_bar.update(len(batch))

#     # Close the progress bar
#     progress_bar.close()

def upsert_pdf_to_qdrant(vector_store: QdrantVectorStore, pdf_path: str, document_id: str):
    loader = PyPDFLoader(pdf_path)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=0,
        length_function=len,
        is_separator_regex=False,
    )

    progress_bar = tqdm(desc="Uploading documents", unit="chunk")

    # TODO: Look at it and if you can processes multiple pages at once, do it.
    pages = []
    MAX_PAGES = 5
    for page in loader.lazy_load():
        pages.append(page)
        if len(pages) < MAX_PAGES:
            continue

        chunks = text_splitter.split_documents(pages)
        for chunk in chunks:
            if not chunk.metadata:
                chunk.metadata = {}
            chunk.metadata["document_id"] = document_id
            chunk.metadata["source"] = pdf_path

            vector_store.add_documents([chunk])
            progress_bar.update(1)
        
        pages.clear()

    progress_bar.close()
