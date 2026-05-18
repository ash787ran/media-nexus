import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import httpx

app = FastAPI(title="Media Nexus Cloud Engine")

# Hardened CORS policy to allow your GitHub Pages to communicate with Render
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
}

async def resolve_imdb_id(title: str) -> tuple[str, str]:
    """Uses the Cinemeta API to resolve movie titles to IMDB IDs."""
    clean_title = httpx.URL(title).path
    search_urls = [
        (f"https://v3-cinemeta.strem.io/catalog/movie/top/search={clean_title}.json", "movie"),
        (f"https://v3-cinemeta.strem.io/catalog/series/top/search={clean_title}.json", "tv")
    ]
    
    async with httpx.AsyncClient(headers=HEADERS, timeout=10.0) as client:
        for url, media_type in search_urls:
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
async def resolve_stream(title: str = Query(..., description="The name of the title")):
    imdb_id, media_type = await resolve_imdb_id(title)
    
    if not imdb_id:
        raise HTTPException(status_code=404, detail="Metadata resolution failed.")
        
    return {
        "title": title.title(),
        "imdb_id": imdb_id,
        "media_type": media_type,
        "endpoints": {
            "primary": f"https://vidsrc.to/embed/{media_type}/{imdb_id}",
            "mirror_alpha": f"https://vidsrc.me/embed/{media_type}?imdb={imdb_id}",
            "mirror_beta": f"https://embed.su/embed/{media_type}/{imdb_id}"
        }
    }

@app.get("/api/v1/health")
async def health_check():
    return {"status": "operational"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
