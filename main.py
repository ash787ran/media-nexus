import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import httpx

app = FastAPI(title="Aether Nexus Stream API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

async def resolve_imdb_id(title: str) -> tuple[str, str]:
    clean_title = httpx.URL(title).path
    urls = [
        (f"https://v3-cinemeta.strem.io/catalog/movie/top/search={clean_title}.json", "movie"),
        (f"https://v3-cinemeta.strem.io/catalog/series/top/search={clean_title}.json", "tv")
    ]
    
    async with httpx.AsyncClient(headers=HEADERS, timeout=7.0) as client:
        for url, media_type in urls:
            try:
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("metas") and len(data["metas"]) > 0:
                        return data["metas"][0].get("imdb_id"), media_type
            except Exception:
                continue
    return None, None

@app.get("/api/v1/resolve")
async def resolve_stream(title: str = Query(..., description="Movie or series name")):
    imdb_id, media_type = await resolve_imdb_id(title)
    
    if not imdb_id:
        raise HTTPException(status_code=404, detail="Target title not found.")
        
    return {
        "title": title,
        "imdb_id": imdb_id,
        "media_type": media_type,
        "endpoints": {
            "primary": f"https://autoembed.co/{media_type}/imdb/{imdb_id}",
            "mirror_alpha": f"https://vidsrc.to/embed/{media_type}/{imdb_id}",
            "mirror_beta": f"https://embed.su/embed/{media_type}/{imdb_id}"
        }
    }

@app.get("/api/v1/health")
async def health_check():
    return {"status": "operational"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
