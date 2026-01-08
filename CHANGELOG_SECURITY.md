# 변경 로그

**프론트엔드 보안 및 UX 개선** 작업과 관련된 모든 주요 변경 사항이 이 파일에 기록됩니다.

이 형식은 [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)을 기반으로 합니다.

## [0.6.43-fix1] - 2026-01-08

### 추가됨

- ⏳ **토큰 만료 카운트다운**: 세션 남은 시간을 사용자에게 알리기 위해 웹 UI(우측 상단)에 카운트다운 타이머가 표시됩니다. <!-- id: 13 -->
- 🔄 **활동 시 토큰 갱신**: 사용 중 세션 만료를 방지하기 위해 사용자 활동(마우스 이동, 키보드 입력 등)에 따라 자동으로 토큰을 갱신하는 로직을 구현했습니다. <!-- id: 12 -->
- 📦 **문서 파싱 라이브러리 추가**: 파일 처리 호환성 강화를 위해 `msoffcrypto-tool`, `chardet`, `nltk`, `pyhwp` 패키지 설치 과정을 Dockerfile에 추가했습니다.
- 🚫 **단일 세션 강제**: 사용자당 하나의 활성 세션만 허용하는 백엔드 로직을 추가했습니다. 새로운 위치에서 로그인하면 이전 세션은 무효화됩니다. <!-- id: 8 -->

### 변경됨

- 💾 **스토리지 마이그레이션**: 탭이나 창을 닫을 때 토큰을 삭제하여 보안을 강화하기 위해 프론트엔드 토큰 저장소를 `localStorage`에서 `sessionStorage`로 이전했습니다. <!-- id: 10 -->
- 🔕 **변경 로그 팝업 비활성화**: 로그인 후 자동으로 나타나는 변경 로그 팝업을 비활성화했습니다.
- 🛡️ **LLM 에러 마스킹**: Ollama 및 OpenAI의 상세 에러 메시지가 프론트엔드에 노출되지 않도록 백엔드 에러 처리를 업데이트했습니다. 사용자는 "오류가 발생했습니다"라는 일반적인 메시지를 보게 되며, 상세 에러는 서버 측에 기록됩니다. <!-- id: 19 -->

### 수정됨

- 🗑️ **토큰 무효화**: 로그아웃 시 토큰이 서버 측에서 즉시 무효화(JTI 제거)되어 재사용되지 않도록 기능을 개선했습니다. <!-- id: 9 -->

## 기술적 세부 사항

- **백엔드**:
  - `backend/open_webui/models/auths.py`: `Auth` 모델에 `token_jti` 필드 추가.
  - `backend/open_webui/routers/auths.py`: `signin`, `signup`, `ldap_auth`에서 JTI를 관리하도록 업데이트. `/refresh` 엔드포인트 추가.
  - `backend/open_webui/utils/auth.py`: `get_current_user`에서 JTI를 검증하도록 업데이트.
  - `backend/open_webui/routers/ollama.py`: `send_post_request`에서 에러 마스킹 처리.
  - `backend/open_webui/routers/openai.py`: `chat/completions`, `proxy`, `embeddings`, `audio/speech` 엔드포인트에서 에러 마스킹 처리.

- **프론트엔드**:
  - `src/routes/auth/+page.svelte`: `sessionStorage`로 전환.
  - `src/routes/(app)/+layout.svelte`: 활동 리스너 및 카운트다운 타이머 추가. `ChangelogModal` 비활성화.
  - `src/lib/apis/auths/index.ts`: `refreshSession` API 호출 추가.
  - `src/lib/components/chat/Messages/Error.svelte`: 일반적인 에러 메시지를 표시하도록 업데이트.
