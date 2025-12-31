from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"ok": True}


@app.get("/users")
def get_users():
    return {
        "service": "user-service",
        "users": [
            {"id": 1, "name": "eve"},
            {"id": 2, "name": "lap"},
            {"id": 3, "name": "ufc"},
            {"id": 4, "name": "F1"},
            {"id": 5, "name": "Max"}

        ]
    }

