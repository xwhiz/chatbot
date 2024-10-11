from fastapi import (
    APIRouter,
    Request,
    Response,
    Form,
    File,
    UploadFile,
    HTTPException,
    status,
)
from fastapi.responses import FileResponse
from bson import ObjectId
from datetime import datetime
from decouple import config
import time

from vectordb_handle import upsert_pdf_to_qdrant, delete_file_from_qdrant


router = APIRouter(prefix="/documents", tags=["Documents"])


@router.get("/count")
async def get_documents_count(request: Request, response: Response):
    # if it's admin, allow else return unauthorized
    payload = request.state.payload
    if payload["role"] != "admin":
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"success": False, "message": "Unauthorized"}

    count = await router.database["documents"].count_documents({})

    return {
        "success": True,
        "message": "Documents count retrieved successfully",
        "data": count,
    }


@router.get("/")
async def get_documents(
    request: Request, response: Response, page: int = 0, limit: int = 10
):
    # if it's admin, allow else return unauthorized
    payload = request.state.payload
    if payload["role"] != "admin":
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"success": False, "message": "Unauthorized"}

    documents = (
        await router.database["documents"]
        .find()
        .skip(page * limit)
        .limit(limit)
        .to_list(length=limit)
    )

    documents = [
        {
            "_id": str(document["_id"]),
            "title": document["title"],
            "created_at": document["created_at"],
        }
        for document in documents
    ]

    return {
        "success": True,
        "message": "Documents retrieved successfully",
        "data": documents,
    }


@router.post("/")
async def create_document(
    request: Request,
    response: Response,
    title: str = Form(...),
    file: UploadFile = File(...),
):
    # Check authorization
    payload = request.state.payload
    if payload["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized"
        )

    # Validate file type
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF files are allowed"
        )

    print("File name:", file.filename)

    import os

    print("received file:", file.filename)

    # Create the directory if it doesn't exist
    if not os.path.exists("uploaded_documents"):
        os.makedirs("uploaded_documents")

    # Save file to disk
    file_location = f"uploaded_documents/{time.time()}{file.filename}"
    with open(file_location, "wb+") as file_obj:
        file_obj.write(await file.read())

    print("File saved to:", file_location)

    # Create document in MongoDB
    document = {
        "title": title,
        "file_path": file_location,
        "created_at": datetime.now(),
    }

    print("Uploading to Qdrant")
    upsert_pdf_to_qdrant(router.vector_store, file_location)
    print("Uploaded to Qdrant")

    result = await router.database["documents"].insert_one(document)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Could not create document"
        )

    if not result.acknowledged:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Could not create document"
        )

    document = {
        "_id": str(result.inserted_id),
        "title": title,
        "file_path": file_location,
        "created_at": document["created_at"],
    }

    response.status_code = status.HTTP_201_CREATED
    return {
        "success": True,
        "message": "Document created successfully",
        "data": document,
    }


@router.get("/{document_id}")
async def get_document(document_id: str, request: Request, response: Response):
    # Check authorization
    payload = request.state.payload
    if payload["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized"
        )

    # Fetch the document from MongoDB
    document = await router.database["documents"].find_one(
        {"_id": ObjectId(document_id)}
    )

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    # Get the file path from the document
    file_path = document.get("file_path")

    if not file_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="File path not found"
        )

    # Serve the file
    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=document["title"] + ".pdf",
    )


@router.delete("/{document_id}")
async def delete_document(document_id: str, request: Request, response: Response):
    # Check authorization
    payload = request.state.payload
    if payload["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized"
        )

    # Fetch the document from MongoDB
    document = await router.database["documents"].find_one(
        {"_id": ObjectId(document_id)}
    )

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    # Get the file path from the document
    file_path = document.get("file_path")

    if not file_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="File path not found"
        )

    delete_file_from_qdrant(router.client, config("COLLECTION_NAME"), file_path)

    # Delete the file from disk
    import os

    os.remove(file_path)

    # Delete the document from MongoDB
    result = await router.database["documents"].delete_one(
        {"_id": ObjectId(document_id)}
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Could not delete document"
        )

    if not result.acknowledged:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Could not delete document"
        )

    return {
        "success": True,
        "message": "Document deleted successfully",
    }
