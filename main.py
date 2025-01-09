

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(host='0.0.0.0', app='app:app', port=8000, reload=True)
    