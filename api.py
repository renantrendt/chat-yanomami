from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from vector_store import VectorStore
import uvicorn

app = FastAPI()
vector_store = VectorStore()

class SearchQuery(BaseModel):
    query: str
    k: int = 3

@app.post("/search")
async def search(query: SearchQuery):
    try:
        results = vector_store.search(query.query, query.k)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/add-content")
async def add_content(texts: list[str]):
    try:
        vector_store.add_content(texts)
        return {"status": "success", "message": f"Added {len(texts)} texts to vector store"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
