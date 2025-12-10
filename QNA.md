# GitHub Agent - LangChain Q&A 문서

## Q1: Agent 초기화 시 Tools에 등록된 기능을 어떻게 입력된 질의에 따라 적절히 호출되는가?

### 내부 작업 처리 과정

LangChain Agent는 다음과 같은 단계를 거쳐 적절한 도구를 선택하고 호출합니다:

#### **Step 1: Agent 초기화**
```python
agent = initialize_agent(
    tools=[get_user_repositories, create_github_issue, ...],
    llm=ChatOpenAI(model="gpt-4"),
    agent=AgentType.OPENAI_FUNCTIONS,
    verbose=True
)
```

이 단계에서 LLM에게 사용 가능한 도구들의 **스키마 정보**를 전달합니다. 각 도구의 이름, 설명, 파라미터 정보를 LLM이 이해할 수 있는 형식으로 변환합니다.

#### **Step 2: 사용자 질의 입력**
```python
result = agent.run("poethera의 저장소 목록을 보여줘")
```

#### **Step 3: Agent의 내부 작동 (가장 중요)**

```
사용자 질의
    ↓
[LLM 분석]
- 질의 텍스트 파싱
- 어떤 도구가 필요한지 판단
- 필요한 파라미터 추출
    ↓
[도구 선택 및 파라미터 결정]
예: 도구="get_user_repositories", 파라미터={"username": "poethera"}
    ↓
[도구 실행]
get_user_repositories(username="poethera") 호출
    ↓
[결과 반환]
저장소 목록 데이터 반환
    ↓
[LLM이 결과 해석]
데이터를 자연어로 포맷팅
    ↓
최종 응답 반환
```

#### **AgentType.OPENAI_FUNCTIONS 방식의 작동**

1. **프롬프트 구성**
   ```
   You are a helpful assistant. You have access to the following tools:
   [도구 1 스키마]
   [도구 2 스키마]
   [도구 3 스키마]
   ...
   
   Use these tools to answer the user's question.
   ```

2. **LLM 호출**
   ```
   LLM에 프롬프트 + 질의 전달
   → LLM이 JSON 형식의 함수 호출 결정
   ```

3. **함수 호출 결과**
   ```python
   {
       "name": "get_user_repositories",
       "arguments": {"username": "poethera"}
   }
   ```

4. **도구 실행 (AgentExecutor)**
   ```python
   tool = tools_dict["get_user_repositories"]
   observation = tool.invoke(arguments)
   ```

5. **반복 여부 판단**
   - LLM이 추가 도구 호출이 필요한지 판단
   - 필요하면 도구 실행 반복
   - 최종 답변 도출 시 종료

#### **구체적인 예시**

```python
# 입력
질의: "poethera의 저장소 목록을 보여줘"

# LLM의 의사결정
→ "get_user_repositories 도구를 사용해야 하고, 
   username 파라미터에 'poethera'를 전달해야 한다"

# 도구 실행
function_call = {
    "name": "get_user_repositories",
    "arguments": {"username": "poethera"}
}
result = get_user_repositories.invoke({"username": "poethera"})

# 결과
result = [
    {"name": "aitry001", "stars": 5, "language": "Python"},
    {"name": "project-x", "stars": 10, "language": "JavaScript"},
    ...
]

# 최종 응답
"poethera님의 저장소는 다음과 같습니다:
1. aitry001 (Python, 5개의 별)
2. project-x (JavaScript, 10개의 별)
..."
```

---

## Q2: Tool 등록 시 어떤 정보를 입력해야 LLM이 올바른 도구를 선택할 수 있는가?

### Tool Schema와 LLM의 도구 선택 메커니즘

#### **Tool Schema 구조**

LangChain의 `@tool` 데코레이터는 Python 함수로부터 다음 정보를 자동 추출합니다:

```python
@tool
def get_user_repositories(username: str) -> List[Dict]:
    """GitHub에서 사용자의 저장소 목록을 가져옵니다
    
    Args:
        username: GitHub 사용자명
        
    Returns:
        저장소 정보 딕셔너리 리스트
    """
```

추출되는 정보:
```json
{
    "name": "get_user_repositories",
    "description": "GitHub에서 사용자의 저장소 목록을 가져옵니다",
    "parameters": {
        "type": "object",
        "properties": {
            "username": {
                "type": "string",
                "description": "GitHub 사용자명"
            }
        },
        "required": ["username"]
    }
}
```

#### **Tool Schema에서 중요한 요소**

| 요소 | 역할 | 중요도 |
|------|------|--------|
| **함수명** | 도구를 식별하는 ID | ⭐⭐⭐ |
| **Docstring (첫 줄)** | 도구의 목적 및 기능 설명 | ⭐⭐⭐⭐⭐ |
| **파라미터 타입** | 입력 데이터 타입 명시 | ⭐⭐⭐⭐ |
| **파라미터 설명** | LLM이 값을 추출하는 가이드 | ⭐⭐⭐⭐⭐ |
| **Returns 타입** | 반환 데이터 구조 | ⭐⭐⭐ |
| **Returns 설명** | 반환값 의미 설명 | ⭐⭐⭐⭐ |

#### **LLM의 도구 선택 의사결정 과정**

```
입력 질의: "poethera의 저장소 목록을 보여줘"
     ↓
[1단계: 의미 분석]
- "저장소 목록" 키워드 추출
- "poethera" = 사용자명
- 작업: "조회"

     ↓
[2단계: Tool Schema와 의미 매칭]
Tool 1: "저장소 목록을 가져옵니다" ✓ 매칭!
Tool 2: "이슈를 생성합니다" ✗ 생성 작업
Tool 3: "코드를 검색합니다" ✗ 검색 작업
Tool 4: "저장소 정보를 조회합니다" ~ 부분 매칭

     ↓
[3단계: 파라미터 추출]
도구: get_user_repositories
파라미터: {"username": "poethera"}

     ↓
최종 선택: get_user_repositories 호출
```

#### **좋은 Tool Schema vs 나쁜 Tool Schema**

**❌ 나쁜 예시:**
```python
@tool
def get_repos(u: str):
    """저장소를 가져옵니다"""
```

**문제점:**
- 너무 짧은 설명
- 파라미터 이름이 모호함 (`u` = username?)
- 타입 힌트 부족
- 반환값 설명 없음
- **LLM의 선택 가능성: 낮음 ❌**

---

**✅ 좋은 예시:**
```python
@tool
def get_user_repositories(username: str) -> List[Dict]:
    """GitHub에서 특정 사용자의 모든 퍼블릭 저장소 목록을 조회합니다.
    
    이 도구는 GitHub API를 사용하여 사용자가 소유한 저장소의 이름, 
    설명, 언어, 별 개수 등의 정보를 반환합니다.
    
    Args:
        username: GitHub 사용자 계정명 (예: 'poethera', 'torvalds')
        
    Returns:
        저장소 정보 딕셔너리 리스트. 각 항목은 name, url, language, 
        stars, description, updated_at를 포함합니다.
    """
```

**장점:**
- 상세한 설명으로 의도가 명확
- 파라미터 예시 제공
- 반환값 구조 설명
- **LLM의 선택 가능성: 높음 ✅**

#### **LLM의 실제 의사결정 프로세스**

```
질의: "poethera의 최근 저장소를 찾아줘"

     ↓
[임베딩 및 의미 분석]
- 키워드: ["poethera", "저장소", "찾아"]
- 의도: 저장소 조회
- 특정 사용자: "poethera"

     ↓
[Tool Schema 검색 및 유사도 계산]

Tool 1 (get_user_repositories):
  "GitHub에서 사용자의 저장소 목록을 가져옵니다"
  유사도: 0.95 ✓ 최고!

Tool 2 (create_github_issue):
  "GitHub에 새 이슈를 생성합니다"
  유사도: 0.10

Tool 3 (search_github_code):
  "GitHub에서 코드를 검색합니다"
  유사도: 0.30

Tool 4 (get_repository_info):
  "저장소의 상세 정보를 조회합니다"
  유사도: 0.40

     ↓
[도구 선택]
유사도 0.95의 get_user_repositories 선택!

     ↓
[파라미터 추출]
description: "GitHub 사용자명"
질의에서: "poethera" 추출
파라미터: {"username": "poethera"}

     ↓
[도구 실행]
get_user_repositories(username="poethera")
```

---

## Q3: LLM에 전달되는 프롬프트는 매 호출마다 입력되는가? Tool Schema는 LangChain이 자동 추출하는가?

### 프롬프트 구조와 Tool Schema 자동 추출

#### **Q3-1: 프롬프트가 매 호출마다 입력되는가?**

**답: 예, 매 호출마다 입력됩니다.**

```python
# 사용자가 호출할 때마다
result = agent.run("poethera의 저장소 목록을 보여줘")  # 호출 1
result = agent.run("이슈를 생성해줘")                 # 호출 2
result = agent.run("Python 코드를 검색해줘")         # 호출 3

# 매번 다음 프롬프트가 LLM에 전달됨:
프롬프트 1: [System Prompt] + [Tool Schema] + "poethera의 저장소 목록을 보여줘"
프롬프트 2: [System Prompt] + [Tool Schema] + "이슈를 생성해줘"
프롬프트 3: [System Prompt] + [Tool Schema] + "Python 코드를 검색해줘"
```

#### **LangChain 내부 코드 흐름**

```python
def agent.run(query):
    # 1. 프롬프트 구성 (매번)
    messages = [
        {"role": "system", "content": system_prompt},  # 시스템 프롬프트
        # Tool Schema가 여기 포함됨
        {"role": "user", "content": query}            # 사용자 질의
    ]
    
    # 2. LLM 호출
    response = llm.predict(messages=messages)
    
    # 3. 도구 실행
    tool_result = execute_tool(response)
    
    # 4. 반복 또는 종료
    ...
```

#### **Q3-2: Tool Schema는 자동 추출되는가?**

**답: 예, LangChain이 자동 추출 및 구조화합니다.**

#### **Tool Schema 자동 추출 과정**

```
입력: Python 함수 객체
    ↓
[Step 1: 함수 메타데이터 추출]
- 함수명: "get_user_repositories"
- Docstring: "GitHub에서 사용자의 저장소 목록을 가져옵니다..."
- 파라미터 정보: username: str

    ↓
[Step 2: 타입 힌트 파싱]
- 파라미터 타입: str
- 반환 타입: List[Dict]

    ↓
[Step 3: JSON Schema 변환]
{
    "type": "object",
    "properties": {
        "username": {
            "type": "string",
            "description": "GitHub 사용자명"
        }
    },
    "required": ["username"]
}

    ↓
[Step 4: Tool Schema 최종 생성]
{
    "name": "get_user_repositories",
    "description": "GitHub에서 사용자의 저장소 목록을 가져옵니다",
    "parameters": {...}
}

    ↓
출력: OpenAI API 형식의 Function Definition
```

#### **LangChain의 Tool 클래스 내부 작동**

```python
# langchain/tools/base.py의 작동 원리

class Tool:
    def __init__(self, func, name=None, description=None):
        self.func = func
        self.name = name or func.__name__  # 함수명 추출
        self.description = description or func.__doc__  # Docstring 추출
        
        # 함수 시그니처 분석
        sig = inspect.signature(func)
        self.args = self._parse_parameters(sig)
        
    def _parse_parameters(self, sig):
        """함수 파라미터를 JSON Schema로 변환"""
        schema = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        for param_name, param in sig.parameters.items():
            # 타입 힌트에서 타입 추출
            param_type = param.annotation
            
            schema["properties"][param_name] = {
                "type": self._python_type_to_json_type(param_type),
                "description": extract_from_docstring(param_name)
            }
            
            if param.default == inspect.Parameter.empty:
                schema["required"].append(param_name)
        
        return schema
    
    def to_openai_function(self):
        """OpenAI Function Calling 형식으로 변환"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.args
        }

# @tool 데코레이터
def tool(func):
    return Tool(func)
```

#### **매 호출 시 프롬프트 구성 과정**

```python
def create_github_agent():
    llm = ChatOpenAI(model="gpt-4", api_key=OPENAI_API_KEY)
    
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

# agent.run("poethera의 저장소 목록을 보여줘") 호출 시:

# [내부 프로세스]
# 1. Agent가 등록된 모든 tools에서 Schema 추출
schemas = [
    tool_1.to_openai_function(),  # get_user_repositories Schema
    tool_2.to_openai_function(),  # create_github_issue Schema
    tool_3.to_openai_function(),  # search_github_code Schema
    tool_4.to_openai_function()   # get_repository_info Schema
]

# 2. 프롬프트 구성
system_prompt = """
You are a helpful assistant. You have access to the following tools:
{schemas_as_json}

Use these tools to answer the user's question.
Respond with JSON: {"action": "tool_name", "action_input": {...}}
"""

messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": "poethera의 저장소 목록을 보여줘"}
]

# 3. LLM 호출 (프롬프트 + Schemas 함께 전달)
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=messages,
    functions=schemas  # ← Tool Schemas가 여기 전달됨
)
```

#### **프롬프트 템플릿과 재사용**

LangChain은 효율성을 위해 **프롬프트 템플릿**을 사용합니다:

```python
# 내부적으로 사용되는 프롬프트 템플릿

SYSTEM_TEMPLATE = """
You are a helpful assistant that has access to the following tools.

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought:"""
```

**매 호출마다:**
1. 템플릿의 `{tools}` 부분에 Tool Schemas 삽입
2. 템플릿의 `{input}` 부분에 사용자 질의 삽입
3. 완성된 프롬프트를 LLM에 전달

#### **정보 흐름 다이어그램**

```
┌─────────────────────────────────────────────────────────┐
│                   Tool 정의 (코드)                       │
│  @tool                                                   │
│  def get_user_repositories(username: str) -> List[Dict]│
│      """GitHub에서 사용자의 저장소 목록..."""              │
└─────────────────────────────────────────────────────────┘
                         ↓
          [LangChain 자동 추출 (1회)]
                         ↓
┌─────────────────────────────────────────────────────────┐
│              Tool Schema (메모리에 저장)                  │
│  {                                                       │
│    "name": "get_user_repositories",                     │
│    "description": "GitHub에서 사용자의 저장소 목록...",   │
│    "parameters": {...}                                  │
│  }                                                       │
└─────────────────────────────────────────────────────────┘
                         ↓
          [매 호출마다 프롬프트 구성]
                         ↓
┌─────────────────────────────────────────────────────────┐
│         프롬프트 (매 호출마다 새로 생성)                  │
│  [System Prompt] + [All Tool Schemas] + [User Query]   │
└─────────────────────────────────────────────────────────┘
                         ↓
            [OpenAI API에 전달]
                         ↓
┌─────────────────────────────────────────────────────────┐
│              LLM 응답 (Tool Selection)                   │
│  {                                                       │
│    "function_call": {                                   │
│      "name": "get_user_repositories",                   │
│      "arguments": {"username": "poethera"}             │
│    }                                                     │
│  }                                                       │
└─────────────────────────────────────────────────────────┘
```

#### **핵심 요점 정리**

| 질문 | 답변 |
|------|------|
| **Tool Schema가 매번 입력되나?** | ✅ 예, 매 호출마다 프롬프트에 포함됨 |
| **Tool Schema는 자동 추출되나?** | ✅ 예, @tool 데코레이터가 함수에서 자동 추출 |
| **추출 시점** | Agent 초기화 시 1회 추출, 메모리에 저장 |
| **프롬프트 전달 시점** | 매 사용자 호출마다 LLM에 전달 |
| **토큰 비용** | Tool Schemas 부분도 토큰으로 계산되므로 비용 발생 |

#### **성능 최적화 팁**

**Tool 설명을 더 간결하게 작성하면:**
- 토큰 수 감소 → API 비용 절감 ✅
- LLM의 처리 속도 증가 ⚡
- 정확도 유지 (설명이 명확하다면) 🎯

---

## 요약

1. **Agent의 도구 선택 메커니즘**
   - LLM이 Tool Schema를 분석하여 의미적으로 가장 적합한 도구 선택
   - 파라미터 추출 및 도구 실행
   - 결과 해석 및 최종 응답 생성

2. **Tool Schema의 정보 중요도**
   - 설명(Description)과 파라미터 설명이 가장 중요
   - 구체적이고 명확한 설명이 정확한 도구 선택을 유도

3. **프롬프트와 Schema의 전달**
   - Tool Schema는 Agent 초기화 시 1회만 추출
   - 프롬프트는 매 호출마다 새로 구성되어 LLM에 전달
   - Tool Schemas도 매번 프롬프트에 포함되어 토큰 비용 발생
