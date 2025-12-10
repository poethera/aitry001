"""
GitHub Agent 테스트 스위트
유닛 테스트 및 통합 테스트를 포함합니다
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# 상위 디렉토리 경로 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from github_agent import (
    get_user_repositories,
    create_github_issue,
    search_github_code,
    get_repository_info
)


class TestGitHubTools(unittest.TestCase):
    """GitHub 도구 함수들의 테스트"""
    
    @patch('github_agent.requests.get')
    def test_get_user_repositories(self, mock_get):
        """저장소 목록 조회 테스트"""
        # Mock 응답 설정
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "name": "test-repo",
                "html_url": "https://github.com/testuser/test-repo",
                "language": "Python",
                "stargazers_count": 10,
                "description": "Test repository",
                "updated_at": "2025-12-10T00:00:00Z"
            }
        ]
        mock_get.return_value = mock_response
        
        # 함수 실행 (invoke 메서드 사용)
        result = get_user_repositories.invoke({"username": "testuser"})
        
        # 검증
        self.assertIsInstance(result, list)
        if isinstance(result, list) and len(result) > 0:
            self.assertIn("name", result[0])
            self.assertIn("url", result[0])
    
    @patch('github_agent.requests.post')
    def test_create_github_issue(self, mock_post):
        """이슈 생성 테스트"""
        # Mock 응답 설정
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "number": 1,
            "title": "Test Issue",
            "html_url": "https://github.com/testuser/test-repo/issues/1",
            "state": "open"
        }
        mock_post.return_value = mock_response
        
        # 함수 실행 (invoke 메서드 사용)
        result = create_github_issue.invoke({
            "owner": "testuser",
            "repo": "test-repo",
            "title": "Test Issue",
            "body": "This is a test issue"
        })
        
        # 검증
        self.assertIsInstance(result, dict)
        if "number" in result:
            self.assertEqual(result["number"], 1)
            self.assertEqual(result["state"], "open")
    
    @patch('github_agent.requests.get')
    def test_search_github_code(self, mock_get):
        """코드 검색 테스트"""
        # Mock 응답 설정
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "items": [
                {
                    "name": "test.py",
                    "repository": {"full_name": "testuser/test-repo"},
                    "html_url": "https://github.com/testuser/test-repo/blob/main/test.py",
                    "path": "test.py"
                }
            ]
        }
        mock_get.return_value = mock_response
        
        # 함수 실행 (invoke 메서드 사용)
        result = search_github_code.invoke({"query": "async def"})
        
        # 검증
        self.assertIsInstance(result, list)
    
    @patch('github_agent.requests.get')
    def test_get_repository_info(self, mock_get):
        """저장소 정보 조회 테스트"""
        # Mock 응답 설정
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "name": "test-repo",
            "description": "Test repository",
            "html_url": "https://github.com/testuser/test-repo",
            "language": "Python",
            "stargazers_count": 10,
            "forks_count": 2,
            "open_issues_count": 3,
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-12-10T00:00:00Z"
        }
        mock_get.return_value = mock_response
        
        # 함수 실행 (invoke 메서드 사용)
        result = get_repository_info.invoke({
            "owner": "testuser",
            "repo": "test-repo"
        })
        
        # 검증
        self.assertIsInstance(result, dict)
        if "name" in result:
            self.assertEqual(result["name"], "test-repo")


class TestErrorHandling(unittest.TestCase):
    """에러 처리 테스트"""
    
    @patch('github_agent.requests.get')
    def test_api_error_handling(self, mock_get):
        """API 에러 처리 테스트"""
        # Mock 에러 응답 설정
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_get.return_value = mock_response
        
        # 함수 실행 (invoke 메서드 사용)
        result = get_user_repositories.invoke({"username": "nonexistent-user"})
        
        # 검증
        self.assertIsInstance(result, dict)
        self.assertIn("error", result)


def run_tests():
    """테스트 실행"""
    # 테스트 스위트 생성
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 테스트 케이스 추가
    suite.addTests(loader.loadTestsFromTestCase(TestGitHubTools))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorHandling))
    
    # 테스트 실행
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    print("=" * 70)
    print("GitHub Agent 테스트 스위트")
    print("=" * 70)
    success = run_tests()
    print("\n" + "=" * 70)
    if success:
        print("✅ 모든 테스트 통과!")
    else:
        print("❌ 일부 테스트 실패")
    print("=" * 70)
