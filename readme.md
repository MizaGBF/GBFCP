# GBF Cors Proxy  
Custom Core Proxy currently used by [GBFAP](https://github.com/MizaGBF/GBFAP).  
Designed to be light-weight and be used on [render.com](https://render.com) free tier.  
  
## Usage(s)  
### Local Testing  
Install the requirements with `python -m pip install requirements.txt` if needed.  
Run the app with `python app.py -debug`.  
Or to emulate its behavior on Render, use `python -m uvicorn app:app --host localhost --port 8001 --timeout-keep-alive=5 --workers=1`.  
  
### On Render  
Use the following start command: `uvicorn app:app --host 0.0.0.0 --timeout-keep-alive=5 --workers=6`.  
Make sure to set the health path to `/health`.