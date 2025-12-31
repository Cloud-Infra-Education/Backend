from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"ok": True}

@app.get("/products")
def get_products():
    return {
        "service": "product-service",
        "products": [
            {"id": "p1", "name": "mouse"},
            {"id": "p2", "name": "monitor"}
        ]
    }

