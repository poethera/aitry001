# GitHub Agent - LangChain을 이용한 GitHub 자동화

GitHub API와 GitHub Copilot을 연결하여 자연어로 GitHub 작업을 수행하는 LangChain 기반 에이전트입니다.

## 📋 프로젝트 개요

이 프로젝트는 LangChain의 Agent 기능을 활용하여 다음과 같은 GitHub 작업을 자동화합니다:

- 📁 사용자의 GitHub 저장소 목록 조회
- 🐛 GitHub 이슈 생성
- 🔍 GitHub 코드 검색
- 📊 저장소 상세 정보 조회

## 🛠 설치 및 환경 설정

### 1. uv 설치

macOS에서 Homebrew 사용:
```bash
brew install uv
```

다른 OS는 [uv 공식 가이드](https://docs.astral.sh/uv/getting-started/installation/)를 참고하세요.

### 2. 프로젝트 설정

```bash
# 가상 환경 생성
uv venv

# 가상 환경 활성화
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate  # Windows

# 의존성 설치
uv pip install -r pyproject.toml
```

또는 한 번에:
```bash
uv sync
```

### 3. 환경 변수 설정

`.env` 파일을 생성하고 다음 정보를 입력하세요:

```env
GITHUB_TOKEN=your_github_token_here
COPILOT_API_KEY=your_copilot_api_key_here
```

**참고**: `.env.example` 파일을 참고하여 작성해주세요.

## 🧪 LangChain 테스트 방법

### 1️⃣ 단위 테스트 실행

기본 테스트 실행:
```bash
python test_github_agent.py
```

더 자세한 출력 원하면:
```bash
python -m unittest test_github_agent.py -v
```

### 2️⃣ 특정 테스트 케이스만 실행

```bash
# 저장소 조회 테스트만
python -m unittest test_github_agent.TestGitHubTools.test_get_user_repositories -v

# 이슈 생성 테스트만
python -m unittest test_github_agent.TestGitHubTools.test_create_github_issue -v

# 코드 검색 테스트만
python -m unittest test_github_agent.TestGitHubTools.test_search_github_code -v

# 저장소 정보 조회 테스트만
python -m unittest test_github_agent.TestGitHubTools.test_get_repository_info -v

# 에러 처리 테스트만
python -m unittest test_github_agent.TestErrorHandling.test_api_error_handling -v
```

### 3️⃣ Coverage를 포함한 테스트

```bash
pip install coverage
coverage run -m unittest test_github_agent.py
coverage report
coverage html  # HTML 리포트 생성
```

### 4️⃣ 실제 Agent 사용

환경 변수가 올바르게 설정되었다면, 다음과 같이 실제 Agent를 테스트할 수 있습니다:

```python
from github_agent import run_agent

# 사용자의 저장소 목록 조회
response = run_agent("poethera의 저장소 목록을 보여줘")
print(response)

# 저장소 정보 조회
response = run_agent("poethera/aitry001의 상세 정보를 알려줘")
print(response)
```

## 📊 테스트 케이스 목록

| 테스트명 | 설명 | 테스트 방식 |
|---------|------|-----------|
| `test_get_user_repositories` | GitHub 사용자의 저장소 목록 조회 | Mock API (requests.get) |
| `test_create_github_issue` | 새 이슈 생성 | Mock API (requests.post) |
| `test_search_github_code` | GitHub 코드 검색 | Mock API (requests.get) |
| `test_get_repository_info` | 저장소 상세 정보 조회 | Mock API (requests.get) |
| `test_api_error_handling` | API 에러 처리 (404 Not Found) | Mock API (requests.get) |

## 🔧 주요 기능

### GitHub 도구 (Tools)

#### 1. `get_user_repositories(username: str)`
GitHub 사용자의 저장소 목록을 조회합니다.

```python
from github_agent import get_user_repositories

repos = get_user_repositories("poethera")
for repo in repos:
    print(f"{repo['name']}: {repo['description']}")
```

#### 2. `create_github_issue(owner: str, repo: str, title: str, body: str)`
GitHub 저장소에 새 이슈를 생성합니다.

```python
from github_agent import create_github_issue

issue = create_github_issue(
    owner="poethera",
    repo="aitry001",
    title="새 기능 추가",
    body="이 기능을 추가해야 합니다."
)
```

#### 3. `search_github_code(query: str)`
GitHub에서 코드를 검색합니다.

```python
from github_agent import search_github_code

results = search_github_code("async def")
for result in results:
    print(f"{result['file']} - {result['repo']}")
```

#### 4. `get_repository_info(owner: str, repo: str)`
GitHub 저장소의 상세 정보를 조회합니다.

```python
from github_agent import get_repository_info

info = get_repository_info("poethera", "aitry001")
print(f"Stars: {info['stars']}")
print(f"Forks: {info['forks']}")
```

## 📦 의존성

- **langchain**: LangChain 프레임워크
- **openai**: OpenAI API 클라이언트
- **python-dotenv**: 환경 변수 관리
- **requests**: HTTP 요청 라이브러리

## 🤖 LangChain Agent 아키텍처

이 프로젝트의 Agent는 다음과 같이 동작합니다:

```
사용자 질의
    ↓
LangChain Agent
    ├─ ChatOpenAI (gpt-4 모델)
    ├─ Tools: [get_user_repositories, create_github_issue, ...]
    └─ AgentType: OPENAI_FUNCTIONS
    ↓
GitHub API 호출
    ↓
결과 반환
```

## ⚠️ 주의사항

1. **API 토큰**: GitHub API와 Copilot API 토큰이 필요합니다.
2. **비용**: OpenAI API 사용에 따른 비용이 발생할 수 있습니다.
3. **Rate Limit**: GitHub API의 Rate Limit을 주의하세요 (시간당 60-5000개 요청).

## 📝 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다.