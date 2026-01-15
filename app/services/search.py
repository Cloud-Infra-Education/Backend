"""
Meilisearch integration service
검색 기능을 Meilisearch와 연동합니다.
"""
import asyncio
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
            # Meilisearch 클라이언트는 동기식이므로 asyncio.to_thread로 실행
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None, 
                lambda: index.search(query, {"limit": limit, "offset": offset})
            )
            return results
        except Exception as e:
            error_str = str(e)
            # 인덱스가 없을 때의 오류 메시지 확인
            if "index_not_found" in error_str.lower() or "not found" in error_str.lower():
                raise ValueError(f"index_not_found: {error_str}")
            raise ValueError(f"Search failed: {error_str}")
    
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
            loop = asyncio.get_event_loop()
            task = await loop.run_in_executor(None, lambda: index.add_documents(documents))
            return task
        except Exception as e:
            raise ValueError(f"Add documents failed: {str(e)}")
    
    async def update_document(
        self,
        index_name: str,
        document: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        문서 업데이트
        
        Args:
            index_name: 인덱스 이름
            document: 업데이트할 문서 (id 포함)
            
        Returns:
            작업 결과
        """
        if not self.client:
            raise ValueError("Meilisearch client not initialized")
        
        try:
            index = self.client.index(index_name)
            loop = asyncio.get_event_loop()
            task = await loop.run_in_executor(None, lambda: index.update_documents([document]))
            return task
        except Exception as e:
            raise ValueError(f"Update document failed: {str(e)}")
    
    async def delete_document(
        self,
        index_name: str,
        document_id: int
    ) -> Dict[str, Any]:
        """
        문서 삭제
        
        Args:
            index_name: 인덱스 이름
            document_id: 삭제할 문서 ID
            
        Returns:
            작업 결과
        """
        if not self.client:
            raise ValueError("Meilisearch client not initialized")
        
        try:
            index = self.client.index(index_name)
            loop = asyncio.get_event_loop()
            task = await loop.run_in_executor(None, lambda: index.delete_document(document_id))
            return task
        except Exception as e:
            raise ValueError(f"Delete document failed: {str(e)}")
    
    async def search_contents(
        self,
        query: str,
        limit: int = 20,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        콘텐츠 검색 (contents 인덱스 전용)
        
        Args:
            query: 검색 쿼리
            limit: 결과 개수 제한
            offset: 결과 오프셋
            
        Returns:
            검색 결과
        """
        return await self.search("contents", query, limit, offset)
    
    async def sync_content(
        self,
        content: Dict[str, Any]
    ) -> bool:
        """
        콘텐츠 동기화 (인덱스에 추가 또는 업데이트)
        
        Args:
            content: 콘텐츠 데이터 (id, title, description, age_rating, like_count)
            
        Returns:
            성공 여부
        """
        if not self.client:
            return False
        
        try:
            index = self.client.index("contents")
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: index.update_documents([content]))
            return True
        except Exception as e:
            print(f"Content sync failed: {str(e)}")
            return False
    
    async def delete_content(self, content_id: int) -> bool:
        """
        콘텐츠 삭제 (인덱스에서 제거)
        
        Args:
            content_id: 콘텐츠 ID
            
        Returns:
            성공 여부
        """
        if not self.client:
            return False
        
        try:
            await self.delete_document("contents", content_id)
            return True
        except Exception as e:
            print(f"Content deletion failed: {str(e)}")
            return False
    
    def is_available(self) -> bool:
        """
        Meilisearch 클라이언트 사용 가능 여부
        
        Returns:
            사용 가능 여부
        """
        return self.client is not None


# 전역 검색 서비스 인스턴스
search_service = SearchService()
