from fastapi import FastAPI

from phonomicon.exports import EXPORTS

app = FastAPI()


@app.get("/abx/functions")
def abx_functions():
    return {"owner": "phonomicon", "functions": EXPORTS}
