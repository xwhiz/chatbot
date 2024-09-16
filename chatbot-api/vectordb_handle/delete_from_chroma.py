from langchain_chroma import Chroma
from decouple import config


persist_directory = config("VECTOR_DOC_DB_PATH")


def delete_file_from_chroma(file_to_delete: str):
    db = Chroma(persist_directory=persist_directory)
    # Get all documents
    results = db.get()

    # Find all IDs associated with the file
    ids_to_delete = []
    for i, metadata in enumerate(results["metadatas"]):
        if "source" in metadata and metadata["source"] == file_to_delete:
            ids_to_delete.append(results["ids"][i])

    # Delete the chunks
    if ids_to_delete:
        db.delete(ids=ids_to_delete)
        print(f"Deleted {len(ids_to_delete)} chunks associated with {file_to_delete}")
    else:
        print(f"No chunks found for {file_to_delete}")


# file_to_delete = "Profile.pdf"
# delete_file_from_chroma(vectordb, file_to_delete)
# print(f"Deleted {file_to_delete} from Chroma")
