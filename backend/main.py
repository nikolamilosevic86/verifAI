import uvicorn

if __name__ == "__main__":
    
    uvicorn.run("verifai_service:app", host="0.0.0.0", port=5001, log_level="info")
    #uvicorn.run("verifai_service:app",workers=2, host="0.0.0.0", port=5001, log_level="info")
