# Open WebUI 커스텀 마이그레이션 가이드 (0.6.43 -> 0.7.2)

본 문서는 Open WebUI 0.6.43 버전에 적용된 커스텀 사항들을 0.7.2 버전으로 이관하기 위한 상세 작업 지침서입니다.

---

## 1. 개요 및 사전 준비

*   **목표**: 보안 강화(세션 스토리지, JTI, 관리자 차단) 및 데이터 정책(채팅 삭제) 기능을 신규 버전에 동일하게 적용.
*   **주의사항**: 0.7.2 버전의 베이스 코드가 변경되었을 수 있으므로, 라인 번호보다는 **코드의 문맥(Context)**을 보고 삽입 위치를 찾으십시오.

---

## 2. 백엔드 (Backend) 변경 사항

### 2.1. 의존성 추가 (`Dockerfile`)
문서 파싱 호환성을 위한 패키지를 추가합니다.

**파일**: `Dockerfile`
```dockerfile
# (기존) RUN pip3 install --no-cache-dir uv && ...
# 아래 내용을 pip3 install 라인에 추가하거나 별도의 RUN 명령어로 추가
RUN pip3 install --no-cache-dir msoffcrypto-tool chardet nltk pyhwp
```

### 2.2. 환경 설정 (`backend/open_webui/env.py`)
새로운 환경 변수를 로드합니다.

**파일**: `backend/open_webui/env.py`
```python
# ... 기존 환경변수 로드 부분 하단에 추가
DISABLE_ADMIN = os.environ.get("DISABLE_ADMIN", "False").lower() == "true"
```

### 2.3. 설정 관리 (`backend/open_webui/config.py`)
`AppConfig` 클래스나 관련 설정 로직에 새 변수를 매핑합니다.

**파일**: `backend/open_webui/config.py`
```python
# ... (상단 import 부분)
from open_webui.env import (
    # ... 기존 import
    DISABLE_ADMIN, # 추가
)

# ... (AppConfig 클래스 내부 혹은 전역 설정 변수)
class AppConfig:
    # ...
    CHAT_DELETE_ENABLED: bool = False
    CHAT_DELETE_DAYS: int = 365
    DISABLE_ADMIN: bool = DISABLE_ADMIN # 추가
    # ...
```

### 2.4. 메인 로직 및 주기적 작업 (`backend/open_webui/main.py`)
채팅 자동 삭제 스케줄러와 프론트엔드로 전달할 설정값을 추가합니다.

**파일**: `backend/open_webui/main.py`
```python
# [Import 추가]
from open_webui.config import (
    # ...
    CHAT_DELETE_ENABLED,
    CHAT_DELETE_DAYS,
)
from open_webui.env import (
    # ...
    DISABLE_ADMIN,
)

# [lifespan 함수 내부] (앱 시작 시 실행되는 로직)
async def lifespan(app: FastAPI):
    # ... (기존 코드)

    # --- [추가 시작] ---
    async def periodic_chat_deletion():
        while True:
            if app.state.config.CHAT_DELETE_ENABLED:
                try:
                    days = app.state.config.CHAT_DELETE_DAYS
                    # log.info(f"Running periodic chat deletion for chats older than {days} days")
                    count = await anyio.to_thread.run_sync(
                        Chats.delete_chats_older_than, days
                    )
                    if count > 0:
                        log.info(f"Deleted {count} old chats")
                except Exception as e:
                    log.error(f"Error in periodic chat deletion: {e}")
            
            # Check every hour
            await asyncio.sleep(60 * 60)

    asyncio.create_task(periodic_chat_deletion())
    # --- [추가 끝] ---
    
    # ...

# [get_app_config 함수 내부] (프론트엔드 config API)
async def get_app_config(request: Request):
    # ...
    return {
        # ...
        "disable_admin": DISABLE_ADMIN, # 추가
        # ...
    }
```

### 2.5. 인증 및 권한 로직 (`backend/open_webui/utils/auth.py`)
관리자 접근 차단 로직을 추가합니다.

**파일**: `backend/open_webui/utils/auth.py`
```python
# [Import 추가]
from open_webui.env import DISABLE_ADMIN

# [get_admin_user 함수 수정]
def get_admin_user(user=Depends(get_current_user)):
    # --- [추가 시작] ---
    if DISABLE_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ERROR_MESSAGES.ACCESS_PROHIBITED,
        )
    # --- [추가 끝] ---

    if user.role != "admin":
        raise HTTPException(...)
    return user
```

### 2.6. 인증 라우터 (`backend/open_webui/routers/auths.py`)
클라이언트와의 시간 동기화를 위해 서버 타임스탬프를 응답에 포함합니다.

**파일**: `backend/open_webui/routers/auths.py`
```python
# [SessionUserResponse 클래스 등 수정]
class SessionUserResponse(Token, UserProfileImageResponse):
    # ...
    server_timestamp: Optional[int] = None # 추가

# [get_session_user, signin 등의 함수 반환값 수정]
# return 문 내의 딕셔너리에 추가:
# "server_timestamp": int(time.time()),
```

### 2.7. 데이터베이스 모델 (`backend/open_webui/models/chats.py`)
오래된 채팅 삭제 메서드를 추가합니다.

**파일**: `backend/open_webui/models/chats.py`
```python
    # [ChatTable 클래스 내부 메서드 추가]
    def delete_chats_older_than(self, days: int) -> int:
        try:
            with get_db() as db:
                cutoff_time = int(time.time()) - (days * 24 * 60 * 60)
                result = (
                    db.query(Chat)
                    .filter(Chat.updated_at < cutoff_time)
                    .delete(synchronize_session=False)
                )
                db.commit()
                return result
        except Exception:
            return 0
```

---

## 3. 데이터베이스 마이그레이션 (DB)

### 3.1. JTI 컬럼 추가
`alembic` 마이그레이션 파일을 생성하거나 수동으로 DB를 업데이트해야 합니다.

**파일**: `backend/open_webui/migrations/versions/xxxx_add_token_jti_to_auth.py` (새로 생성)
```python
"""add token_jti to auth"""
from alembic import op
import sqlalchemy as sa

# revision identifiers... (자동 생성됨)

def upgrade():
    op.add_column('auth', sa.Column('token_jti', sa.String(), nullable=True))

def downgrade():
    op.drop_column('auth', 'token_jti')
```

---

## 4. 프론트엔드 (Frontend) 변경 사항

### 4.1. 스토리지 변경 (전역) **[중요]**
프로젝트 전체에서 `localStorage`에 저장되는 토큰 로직을 `sessionStorage`로 변경해야 합니다.
**대상 파일**: `src/lib/apis/index.ts`, `src/routes/+layout.svelte`, 인증 관련 파일들.

*   **검색**: `localStorage.token` 또는 `localStorage.getItem('token')`
*   **변경**: `sessionStorage.token` 또는 `sessionStorage.getItem('token')`

### 4.2. API 클라이언트 (`src/lib/apis/index.ts`)
토큰 참조 위치 변경. (위의 4.1에 포함됨)

### 4.3. 레이아웃 및 보안 로직 (`src/routes/+layout.svelte`)
세션 타임아웃 감지 및 글로벌 401 인터셉터 추가.

**파일**: `src/routes/+layout.svelte`
```javascript
// [onMount 내부]

// 1. Global Fetch Interceptor for 401 Unauthorized handling
const originalFetch = window.fetch;
window.fetch = async (...args) => {
    const response = await originalFetch(...args);
    if (response.status === 401) {
        // ... (인증 헤더 확인 로직)
        if (hasAuthHeader) {
            console.warn('Global 401 Interceptor: Redirecting to auth.');
            // 스토리지 클리어
            if (localStorage.getItem('token')) localStorage.removeItem('token');
            if (sessionStorage.getItem('token')) sessionStorage.removeItem('token');
            window.location.href = '/auth'; // 강제 리다이렉트
            return new Response(null, { status: 401 });
        }
    }
    return response;
};

// 2. 소켓 연결 시 sessionStorage 사용 (기존 localStorage 대체)
// 3. getSessionUser 호출 시 sessionStorage 사용
```

### 4.4. 인증 페이지 (`src/routes/auth/+page.svelte`)
로그인 완료 시 토큰 저장소를 `sessionStorage`로 설정하고, 이미 로그인된 유저 체크 로직 수정.

**파일**: `src/routes/auth/+page.svelte`
```javascript
// onMount 체크 로직
if ($user) { // $user가 존재하면 리다이렉트
    goto(redirectPath || '/');
}
```

### 4.5. 관리자 페이지 차단 (`src/routes/(app)/admin/+layout.svelte`)
프론트엔드 단에서도 관리자 페이지 접근을 막습니다.

**파일**: `src/routes/(app)/admin/+layout.svelte`
```javascript
import { config } from '$lib/stores'; // config 스토어 import

onMount(async () => {
    // disable_admin 체크 추가
    if ($user?.role !== 'admin' || $config?.features?.disable_admin) {
        await goto('/');
    }
    // ...
});
```

### 4.6. 신규 컴포넌트: 세션 타임아웃 모달
**파일 생성**: `src/lib/components/layout/Overlay/SessionTimeoutModal.svelte`
(0.6.43 버전의 해당 파일 전체 코드를 복사하여 생성)

### 4.7. 모달 닫기 방지 수정 (`src/lib/components/common/Modal.svelte`)
약관 동의 등 중요 모달이 닫히지 않도록 수정합니다.

**파일**: `src/lib/components/common/Modal.svelte`
```javascript
// [script]
export let dismissible = true; // prop 추가 또는 확인

// [HTML 구조]
// 배경 클릭 이벤트(on:click)나 키보드 이벤트(on:keydown)에서
// dismissible 값이 false이면 close() 함수가 실행되지 않도록 조건문 추가.
```

---

## 5. 최종 확인 체크리스트

1.  [ ] **빌드 테스트**: `npm run build` 및 백엔드 실행 시 에러가 없는가?
2.  [ ] **세션 동작**: 로그인 후 브라우저 탭을 닫고 다시 열었을 때 로그아웃 상태인가? (`sessionStorage` 확인)
3.  [ ] **채팅 삭제**: `CHAT_DELETE_ENABLED=true` 설정 후 오래된 채팅이 삭제되는가? (로그 확인)
4.  [ ] **관리자 차단**: `DISABLE_ADMIN=true` 설정 후 관리자 메뉴 접근 시 메인으로 튕기는가?
5.  [ ] **401 처리**: 토큰 만료(또는 조작) 후 API 요청 시 로그인 페이지로 이동하는가?
6.  [ ] **모달 방지**: 필수 모달이 배경 클릭으로 닫히지 않는가?

---
*Generated by Antigravity*
