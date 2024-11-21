from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import StreamingResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import aiohttp
import aiofiles
import json
from base64 import b64encode
from io import BytesIO
import os
import sys
import shutil
import logging

app = FastAPI()
etag = None
if "-debug" not in sys.argv:
    origin = "https://mizagbf.github.io"
else:
    origin = "*"
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin],
    allow_credentials=True,
    allow_methods=["get"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware)
logging.basicConfig(level=logging.INFO)

class GBFCP():
    def __init__(self):
        self.manifestUri = "https://prd-game-a-granbluefantasy.akamaized.net/assets_en/js/model/manifest/"
        self.cjsUri = "https://prd-game-a-granbluefantasy.akamaized.net/assets_en/js/cjs/"
        self.imgUri = "https://prd-game-a-granbluefantasy.akamaized.net/assets_en/img"
        self.client = None
        self.count = 0

    async def request(self, url):
        if self.client is None: self.client = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20))
        response = await self.client.get(url, headers={'connection':'keep-alive', 'accept-encoding': 'gzip, deflate'})
        async with response:
            if response.status != 200: raise Exception()
            return await response.read()

    async def getEtag(self):
        global etag
        if etag is None:
            try:
                res = await self.request('https://raw.githubusercontent.com/MizaGBF/GBFAP/main/json/changelog.json')
                etag = str(json.loads(res.decode('utf-8'))['timestamp'])
            except:
                return "abcdefghijklmnopqrstuvwxyz"
        return etag

    def check_disk_state(self):
        total_size = 0
        for dirpath, dirnames, filenames in os.walk('store'):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total_size += os.path.getsize(fp)
        if total_size >= 838860800: # 800 MB
            shutil.rmtree('store')

    async def getAsset(self, url):
        url = url.replace("http://", "https://")
        fn = b64encode(url.encode('utf-8')).decode('utf-8')
        try:
            async with aiofiles.open("store/assets/" + fn, mode="rb") as f:
                data = await f.read()
            return BytesIO(data)
        except:
            try: os.makedirs(os.path.dirname("store/assets/"), exist_ok=True)
            except: pass
            try:
                data = await self.request(url)
                self.count += 1
                if self.count >= 200:
                    self.check_disk_state()
                    self.count = 0
                async with aiofiles.open("store/assets/" + fn, mode="wb") as f:
                    await f.write(data)
                return BytesIO(data)
            except:
                return None

    async def getJS(self, js):
        handle = await self.getAsset(self.manifestUri + js + ".js")
        data = handle.read()
        handle.close()
        return await self.processManifest(js + ".js", data.decode('utf-8'))

gbfcp = GBFCP()

@app.get('/health', status_code=200)
async def render_health_check():
    return {"result": "ok"}

@app.get('/assets/test.png', status_code=200)
async def process_test():
    return {"result": "ok"}

@app.get('/{subpath:path}')
async def process_normal(subpath : str, if_none_match: str | None = Header(default=None)):
    if subpath.startswith("https://prd-game-a") and "-granbluefantasy.akamaized.net" in subpath:
        if await gbfcp.getEtag() == if_none_match:
            return Response(status_code=304)
        # do stuff
        subpath = subpath.split('?')[0]
        data = await gbfcp.getAsset(subpath)
        if data is not None:
            if subpath.endswith(".js"):
                return StreamingResponse(data, media_type="application/javascript", headers={"ETag": etag, "Cache-Control": "public, max-age=2678400, stale-if-error=86400", "Access-Control-Allow-Origin":origin})
            elif subpath.endswith(".png"):
                return StreamingResponse(data, media_type="image/png", headers={"ETag": etag, "Cache-Control": "public, max-age=2678400, stale-if-error=86400", "Access-Control-Allow-Origin":origin})
            elif subpath.endswith(".jpg"):
                return StreamingResponse(data, media_type="image/jpeg", headers={"ETag": etag, "Cache-Control": "public, max-age=2678400, stale-if-error=86400", "Access-Control-Allow-Origin":origin})
        raise HTTPException(
            status_code=404,
            detail="Item not found"
        )
    else:
        raise HTTPException(
            status_code=404,
            detail="Item not found"
        )

if __name__ == "__main__":
    if '-debug' in sys.argv:
        import uvicorn
        uvicorn.run(app, port=8001)