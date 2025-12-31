from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"ok": True}

@app.get("/orders")
def get_orders():
    return {
        "service": "order-service",
        "orders": [
            {"order_id": 101, "item": "laptop"},
            {"order_id": 102, "item": "keyboard"},
            {"order_id": 103, "item": "kup"}
        ]
    }

