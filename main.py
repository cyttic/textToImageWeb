import base64
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional

import renderer

app = FastAPI(title="Hebrew Text Renderer")
app.mount("/static", StaticFiles(directory="static"), name="static")


class RenderRequest(BaseModel):
    text: str
    font_file: str
    font_size: int = 60
    bg: str = "#ffffff"
    fg: str = "#1a1a1a"
    bg_image: Optional[str] = None


@app.get("/", response_class=HTMLResponse)
def index():
    with open("static/HebrewTextRenderer.html", encoding="utf-8") as f:
        return f.read()


@app.get("/fonts")
def fonts():
    return renderer.list_fonts()


@app.get("/backgrounds")
def backgrounds():
    return renderer.list_backgrounds()


@app.get("/backgrounds/{filename}")
def background_image(filename: str):
    path = renderer.get_background_path(filename)
    if not path:
        raise HTTPException(404, "Background not found")
    return FileResponse(path)


@app.post("/render")
def render(req: RenderRequest):
    """Display render — transparent background so HTML paper shows through."""
    path = renderer.get_font_path(req.font_file)
    if not path:
        raise HTTPException(404, f"Font not found: {req.font_file}")
    try:
        png = renderer.render(
            text=req.text, font_path=path, font_size=req.font_size,
            bg=req.bg, fg=req.fg, transparent=True,
        )
        return JSONResponse({"image": base64.b64encode(png).decode()})
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/download")
def download(req: RenderRequest):
    """Export render — solid or texture background, returns raw PNG."""
    path = renderer.get_font_path(req.font_file)
    if not path:
        raise HTTPException(404, f"Font not found: {req.font_file}")
    try:
        png = renderer.render(
            text=req.text, font_path=path, font_size=req.font_size,
            bg=req.bg, fg=req.fg,
            bg_image=req.bg_image,
            transparent=False,
        )
        return Response(content=png, media_type="image/png",
                        headers={"Content-Disposition":
                                 'attachment; filename="hebrew_text.png"'})
    except Exception as e:
        raise HTTPException(500, str(e))
