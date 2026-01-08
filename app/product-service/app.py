os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from common.database import get_db_connection
from common.logger import get_request_info

app = FastAPI()

@app.get("/search")
def search_products(q: str = Query(None, min_length=2)):
    # 1. 추적 정보 및 리전 가져오기
    trace_id, region = get_request_info()


