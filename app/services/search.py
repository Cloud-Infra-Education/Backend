"""
Meilisearch integration service
검색 기능을 Meilisearch와 연동합니다.
"""
from typing import Optional, List, Dict, Any
from meilisearch import Client
from app.core.config import settings


class SearchService:
    """Meilisearch 검색 서비스"""
    
    def __init__(self):
        self.client: Optional[Client] = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Meilisearch 클라이언트 초기화"""
        if settings.MEILISEARCH_URL:
            self.client = Client(
                settings.MEILISEARCH_URL,
                api_key=settings.MEILISEARCH_API_KEY
            )
    
    async def search(
        self,
        index_name: str,
        query: str,
        limit: int = 20,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        검색 수행
        
        Args:
            index_name: 검색할 인덱스 이름
            query: 검색 쿼리
            limit: 결과 개수 제한
            offset: 결과 오프셋
            
        Returns:
            검색 결과
        """
        if not self.client:
            raise ValueError("Meilisearch client not initialized")
        
        try:
            index = self.client.index(index_name)
            results = index.search(query, {"limit": limit, "offset": offset})
            return results
        except Exception as e:
            raise ValueError(f"Search failed: {str(e)}")
    
    async def add_documents(
        self,
        index_name: str,
        documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        문서 추가
        
        Args:
            index_name: 인덱스 이름
            documents: 추가할 문서 리스트
            
        Returns:
            작업 결과
        """
        if not self.client:
            raise ValueError("Meilisearch client not initialized")
        
        try:
            index = self.client.index(index_name)
            task = index.add_documents(documents)
            return task
        except Exception as e:
            raise ValueError(f"Add documents failed: {str(e)}")


# 전역 검색 서비스 인스턴스
search_service = SearchService()
