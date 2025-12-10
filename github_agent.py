"""
GitHub Agent using LangChain with GitHub Copilot
GitHub API와 GitHub Copilot을 연결하여 자연어로 GitHub 작업을 수행하는 에이전트
"""

import os
from typing import List, Dict
import requests
from langchain.tools import tool
from langchain.agents import initialize_agent, AgentType
from langchain.chat_models import ChatOpenAI
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
COPILOT_API_KEY = os.getenv("COPILOT_API_KEY")

if not GITHUB_TOKEN:
    raise ValueError("GITHUB_TOKEN 환경변수가 설정되지 않았습니다")
if not COPILOT_API_KEY:
    raise ValueError("COPILOT_API_KEY 환경변수가 설정되지 않았습니다")


# ========== 도구(Tools) 정의 ==========

@tool
def get_user_repositories(username: str) -> List[Dict]:
    """GitHub에서 사용자의 저장소 목록을 가져옵니다
    
    Args:
        username: GitHub 사용자명
        
    Returns:
        저장소 정보 딕셔너리 리스트
    """
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    url = f"https://api.github.com/users/{username}/repos"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        repos = response.json()
        return [
            {
                "name": repo["name"],
                "url": repo["html_url"],
                "language": repo["language"],
                "stars": repo["stargazers_count"],
                "description": repo["description"],
                "updated_at": repo["updated_at"]
            }
            for repo in repos
        ]
    else:
        return {"error": f"Status code: {response.status_code}", "message": response.text}


@tool
def create_github_issue(owner: str, repo: str, title: str, body: str) -> Dict:
    """GitHub에 새 이슈를 생성합니다
    
    Args:
        owner: 저장소 소유자
        repo: 저장소명
        title: 이슈 제목
        body: 이슈 본문
        
    Returns:
        생성된 이슈 정보
    """
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    data = {"title": title, "body": body}
    
    response = requests.post(url, json=data, headers=headers)
    
    if response.status_code == 201:
        issue = response.json()
        return {
            "number": issue["number"],
            "title": issue["title"],
            "url": issue["html_url"],
            "state": issue["state"]
        }
    else:
        return {"error": f"Status code: {response.status_code}", "message": response.text}


@tool
def search_github_code(query: str) -> List[Dict]:
    """GitHub에서 코드를 검색합니다
    
    Args:
        query: 검색 쿼리
        
    Returns:
        검색 결과 리스트
    """
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    url = "https://api.github.com/search/code"
    params = {"q": query, "per_page": 5}
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        results = response.json()
        return [
            {
                "file": item["name"],
                "repo": item["repository"]["full_name"],
                "url": item["html_url"],
                "path": item["path"]
            }
            for item in results.get("items", [])
        ]
    else:
        return {"error": f"Status code: {response.status_code}", "message": response.text}


@tool
def get_repository_info(owner: str, repo: str) -> Dict:
    """GitHub 저장소의 상세 정보를 조회합니다
    
    Args:
        owner: 저장소 소유자
        repo: 저장소명
        
    Returns:
        저장소 정보 딕셔너리
    """
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    url = f"https://api.github.com/repos/{owner}/{repo}"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        repo_data = response.json()
        return {
            "name": repo_data["name"],
            "description": repo_data["description"],
            "url": repo_data["html_url"],
            "language": repo_data["language"],
            "stars": repo_data["stargazers_count"],
            "forks": repo_data["forks_count"],
            "open_issues": repo_data["open_issues_count"],
            "created_at": repo_data["created_at"],
            "updated_at": repo_data["updated_at"]
        }
    else:
        return {"error": f"Status code: {response.status_code}", "message": response.text}


# ========== Agent 초기화 ==========

def create_github_agent():
    """GitHub Agent를 초기화합니다"""
    llm = ChatOpenAI(
        model="gpt-4",
        temperature=0,
        api_key=COPILOT_API_KEY,
        base_url="https://api.githubcopilot.com/v1"
    )
    
    tools = [
        get_user_repositories,
        create_github_issue,
        search_github_code,
        get_repository_info
    ]
    
    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.OPENAI_FUNCTIONS,
        verbose=True
    )
    
    return agent


def run_agent(query: str) -> str:
    """사용자 질의를 처리합니다
    
    Args:
        query: 사용자의 자연어 질의
        
    Returns:
        Agent의 응답
    """
    agent = create_github_agent()
    result = agent.run(query)
    return result


if __name__ == "__main__":
    # 테스트 쿼리 예시
    test_queries = [
        "poethera의 저장소 목록을 보여줘",
        "poethera/aitry001의 상세 정보를 알려줘",
    ]
    
    print("=" * 60)
    print("GitHub Agent 테스트 시작")
    print("=" * 60)
    
    for query in test_queries:
        print(f"\n[질의] {query}")
        print("-" * 60)
        try:
            response = run_agent(query)
            print(f"[응답]\n{response}")
        except Exception as e:
            print(f"[에러] {str(e)}")
        print("=" * 60)
