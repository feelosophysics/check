# 🤝 미션 비교 & 피어 러닝 토론 리포트
> **대상 미션**: 순수 HTML/CSS/JS로 만드는 반응형 포트폴리오 (`mission.md`)  
> **비교 대상**: `bc` ([feelosophysics](file:///Users/f22losophysics1091/Desktop/CS.B4-1/bc)) vs `sh` ([Sihyun Kim](file:///Users/f22losophysics1091/Desktop/CS.B4-1/sh))  
> **작성 목적**: 학습 동료와 코드 미팅 시 깊이 있는 의견 교환 및 React 진입 전 웹 동작 원리의 공동 체득

---

## 🎯 1단계: 미션의 핵심 함의와 학습 목표

본 미션은 단순히 포트폴리오 웹사이트를 제작하는 데 그치지 않고, **React/Vue 등 프레임워크로 넘어가기 전 순수 웹 표준(Vanilla Web)의 근본 원리를 체득**하는 것에 핵심 목표가 있습니다.

### 1. 왜 순수 HTML/CSS/JS로 먼저 작성해야 할까?
* **브라우저 렌더링 파이프라인의 이해**: HTML 파싱 $\rightarrow$ DOM 트리 생성 $\rightarrow$ CSSOM 합류 $\rightarrow$ Render Tree $\rightarrow$ Layout $\rightarrow$ Paint 과정을 직접 경험해야 프레임워크의 가상 DOM(Virtual DOM)이나 SSR/CSR의 이점을 이해할 수 있습니다.
* **추상화 레이어 아래의 동작 원리**: React의 `useState`, `useEffect`, JSX는 결국 브라우저의 `addEventListener`, `fetch`, `document.createElement`/`innerHTML`을 추상화한 것입니다.
* **이벤트 기반 데이터 흐름 체득**: `사용자 이벤트 → 상태(State) 변경 → DOM 업데이트`로 이어지는 단방향/양방향 데이터 흐름의 원형을 직접 구축해보는 미션입니다.

---

## 📊 2단계: `bc` vs `sh` 핵심 설계 및 코드 차이 비교

두 사람의 코드베이스를 비교하면, 미션 해결을 바라보는 **아키텍처적 관점의 차이**가 명확히 드러납니다.

### 📌 종합 비교 요약표

| 비교 항목 | `bc` (feelosophysics) | `sh` (Sihyun Kim) | 학습 및 토론 포인트 |
| :--- | :--- | :--- | :--- |
| **JS 파일 구조** | 단일 `js/main.js` 중심 구조 | ES Modules (`import`/`export`) 기반 모듈화 구조 | 파일 분리 및 모듈 의존성 관리 |
| **상태 관리 방식** | 중앙 집중식 `STATE` 객체 기반 (단방향 렌더링) | 기능별 DOM 요소 직접 조작 및 로컬 상태 분산 | React의 `useState` & Single Source of Truth |
| **다크모드 FOUC 방지** | `STATE` 및 `main.js` (`defer`)에서 초기화 | `<head>` 내 **동기식 인라인 스크립트**로 FOUC 완벽 방지 | 브라우저 렌더링 순서와 깜빡임(FOUC) 해결 |
| **CSS 구조화** | 단일 `css/style.css` (모바일 퍼스트) | 13개 세부 파일로 컴포넌트별 CSS 모듈화 | CSS 유지보수 전략 및 CSS-in-JS pre-cursor |
| **GitHub API & 프로젝트** | 저장소 원본 데이터 보관 + **언어별 필터링** | API 통신(`api.js`)과 DOM 생성(`ui.js`) 분리 | 비동기 상태(Loading/Success/Error/Empty) |
| **Form UX & API** | **Formspree 연동** (실제 전송) + 실시간 검증 | 순수 JS 검증 + alert 안내 | 폼 데이터 검증 방식 및 외부 API integration |
| **문서화 (Documentation)** | `study/` 폴더 내 상세 가이드 및 정리 자료 제공 | README에 시맨틱 태그 및 Grid/Flex 개념 정리 | 학습 기록 및 기술 블로그/README 작성 습관 |

---

### 🔍 세부 코드 딥다이브

#### 1. JavaScript 아키텍처: 중앙 STATE 객체 vs ES Modules 컴포넌트 분리

* **`sh`의 모듈화 구조 ([main.js](file:///Users/f22losophysics1091/Desktop/CS.B4-1/sh/js/main.js))**
  ES6 Modules를 적극 도입하여 역할에 따라 파일과 컴포넌트를 깨끗하게 분리했습니다.
  ```javascript
  // sh/js/main.js
  import { initNavbar } from "./components/navbar.js";
  import { initDarkMode } from "./components/darkmode.js";
  import { initProjects } from "./components/projects.js";
  import { initContact } from "./components/contact.js";
  import { initScroll } from "./components/scroll.js";
  import { initTyping } from "./components/typing.js";

  initNavbar();
  initDarkMode();
  initProjects();
  initContact();
  initScroll();
  initTyping();
  ```
  > **장점**: 컴포넌트 단위로 책임이 나뉘어 코드 탐색이 직관적이며, 확장성이 뛰어납니다.

* **`bc`의 중앙 상태 관리 ([main.js](file:///Users/f22losophysics1091/Desktop/CS.B4-1/bc/portfolio/js/main.js#L7-L18))**
  애플리케이션의 모든 상태를 하나의 객체로 모으고, 상태가 변경되면 렌더 함수를 명시적으로 호출하는 React/Redux 스타일을 채택했습니다.
  ```javascript
  // bc/portfolio/js/main.js
  const STATE = {
    theme: localStorage.getItem('theme') || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'),
    portfolio: {
      allData: [],
      filter: 'all',
      status: 'idle',
      errorMsg: ''
    }
  };

  const renderProjectsUI = () => {
    const { status, allData, filter, errorMsg } = STATE.portfolio;
    // status에 따라 Loading / Error / Empty / Success(filteredData) DOM 렌더링
  };
  ```
  > **장점**: UI의 상태 변화 추적이 용이하며, 데이터와 UI가 동기화되지 않는 버그를 방지합니다.

---

#### 2. 다크 모드 초기화와 FOUC(Flash of Unstyled Content) 방지

페이지가 로드될 때 흰 화면이 잠깐 반짝였다가 다크 모드로 바뀌는 현상을 **FOUC**라고 합니다.

* **`sh`의 해결책 ([index.html](file:///Users/f22losophysics1091/Desktop/CS.B4-1/sh/index.html#L9-L16))**
  HTML의 `<head>` 영역 안에서 외부 CSS/JS보다 먼저 실행되는 **동기식 인라인 스크립트**를 작성하여 DOM이 그려지기 직전에 `dataset.theme`을 주입했습니다.
  ```html
  <head>
      <script>
          const savedTheme = localStorage.getItem("theme");
          if (savedTheme) {
              document.documentElement.dataset.theme = savedTheme;
          } else if (window.matchMedia("(prefers-color-scheme: dark)").matches) {
              document.documentElement.dataset.theme = "dark";
          }
      </script>
      <link rel="stylesheet" href="css/style.css">
  </head>
  ```
  > **Insight**: 브라우저 렌더링 차단 스크립트(Render Blocking)의 특징을 오히려 다크 모드 깜빡임 방지에 우수하게 활용한 모범 사례입니다!

---

#### 3. 외부 API 처리 및 4가지 UI 상태 (Loading / Success / Error / Empty)

* **`sh`의 역할 분리 ([api.js](file:///Users/f22losophysics1091/Desktop/CS.B4-1/sh/js/api.js) & [ui.js](file:///Users/f22losophysics1091/Desktop/CS.B4-1/sh/js/ui.js))**
  API 요청 로직(`api.js`)과 HTML 문자열 생성 로직(`ui.js`), 그리고 렌더링 오케스트레이션(`projects.js`)을 차분히 분리했습니다.
  ```javascript
  // sh/js/api.js
  export async function fetchRepositories(username) {
      const response = await fetch(`https://api.github.com/users/${username}/repos`);
      if (!response.ok) throw new Error("GitHub API 호출 실패");
      return await response.json();
  }
  ```

* **`bc`의 데이터 가공 및 보너스 미션 ([main.js](file:///Users/f22losophysics1091/Desktop/CS.B4-1/bc/portfolio/js/main.js#L186-L240))**
  API 응답에서 fork 저장소를 제외(`!repo.fork`)하고, 선택한 언어로 실시간 필터링(`Array.prototype.filter`)하는 보너스 기능을 완벽하게 구현했습니다.
  ```javascript
  // bc/portfolio/js/main.js
  const filteredData = filter === 'all'
    ? allData
    : allData.filter(repo => repo.language === filter);
  ```

---

## 🗣️ 3단계: 동료와 함께 나눌 5가지 심도 있는 대화 주제 & 코드 포인트

미팅 시 아래 5가지 포인트를 중심으로 대화를 나누면 서로의 코드를 깊이 있게 이해하고 학습 효과를 극대화할 수 있습니다.

---

### 💬 [주제 1] 프론트엔드 코드 모듈화: ES Modules(SH) vs 중앙 집중식 STATE(BC)
> **대화 질문**: "시현님은 ES Modules로 파일과 컴포넌트를 분리하셨고, 저는 단일 파일 내에서 `STATE` 객체로 데이터 흐름을 묶었는데요. 미션을 진행하시면서 모듈 분리 시 가장 고민되었던 점은 무엇이었나요? 다음 미션인 React로 넘어가면 이 두 방식이 어떻게 결합될까요?"

* **토론 포인트**:
  * SH의 모듈화 구조는 React의 **컴포넌트 분리 (`import ReactComponent from ...`)**의 기초가 됩니다.
  * BC의 중앙 STATE 구조는 React의 **`useState` / `useReducer` / `Zustand` 상태 관리**의 기초가 됩니다.
  * 두 구조를 합성하면 "모듈화된 컴포넌트 + 중앙 상태 관리"라는 최신 프론트엔드 아키텍처가 완성됨을 공유합니다.

---

### 💬 [주제 2] 다크모드와 브라우저 렌더링 파이프라인 (FOUC 방지 칭찬 포인트!)
> **대화 질문**: "시현님의 HTML `<head>`에 있는 인라인 스크립트를 보고 정말 감탄했습니다! 새로고침 시 다크모드 깜빡임(FOUC) 현상을 잡기 위해 이 방법을 선택하게 된 계기가 궁금합니다."

* **토론 포인트**:
  * `<script defer>`와 `<head>` 내부 인라인 `<script>`의 실행 시점 차이 분석.
  * 브라우저가 HTML을 읽다가 `<script>`를 만났을 때 렌더링을 멈추는(Blocking) 특성이 FOUC 해결에 어떻게 기여했는지 함께 논의.
  * BC의 `prefers-color-scheme` 체인과 SH의 FOUC 방지 스크립트를 결합한 '이상적인 다크모드 초기화 로직' 작성해보기.

---

### 💬 [주제 3] API 비동기 처리 및 UI 4대 상태(Loading/Success/Error/Empty) 패턴
> **대화 질문**: "GitHub API 요청 시 네트워크 지연이나 에러(403 Rate Limit 등)가 일어났을 때 사용자에게 어떤 UI를 보여주도록 처리하셨나요? `try...catch` 및 재시도(Retry) 버튼 동작 흐름을 비교해봐요."

* **토론 포인트**:
  * 로딩 중 스피너 표시 $\rightarrow$ 성공 시 데이터 렌더링 $\rightarrow$ 실패 시 재시도 버튼 제공 흐름 확인.
  * BC의 `Array.prototype.filter`를 통한 언어별 필터링 기능(`All`, `JavaScript`, `Python` 등) 구현 노하우 공유.
  * SH의 `api.js`와 `ui.js`로 함수를 쪼개어 가독성을 높인 부분 피드백.

---

### 💬 [주제 4] CSS 스타일링 전략: 13개 세부 파일 분리 vs BEM & 단일 파일
> **대화 질문**: "시현님은 CSS를 `header.css`, `projects.css`, `responsive.css` 등 13개 파일로 매우 세밀하게 나누셨는데요, 파일 분리가 스타일 수정 시 얼마나 편리하셨나요?"

* **토론 포인트**:
  * SH의 CSS 파일 분리 전략 vs BC의 BEM 네이밍 규칙(`hero__title`, `btn--primary`) 장단점 비교.
  * CSS Variables (`:root`)로 테마 컬러 및 간격 시스템을 구축한 방식 비교.
  * 모바일 퍼스트(`min-width`) 미디어 쿼리 작성 경험 공유.

---

### 💬 [주제 5] Form UX: 실시간 입력 검증(Input) vs 실제 이메일 전송(Formspree)
> **대화 질문**: "Contact 섹션에서 폼 검증과 사용자 피드백을 어떻게 처리하셨나요? 저는 Formspree를 연동해 실제 메일이 발송되도록 했는데, 시현님의 검증 방식과 함께 서비스 완성도를 높이는 방법을 이야기해보고 싶습니다."

* **토론 포인트**:
  * 제출 시(`submit`) 검증과 입력 시(`input`) 에러 실시간 해제 UX 비교.
  * `event.preventDefault()`의 역할과 폼 기본 동작 차단.
  * Formspree 연동을 통한 포트폴리오의 실용성 향상 방안 대화.

---

## 💡 결론 및 다음 단계 (React 연결)

이번 미션을 통해 두 분 모두 순수 HTML/CSS/JS 수준에서 **웹 기초 역량**을 훌륭히 다졌습니다.

1. **SH의 강점**: 뛰어난 모듈화(`import/export`), FOUC 방지 혜안, 깔끔한 역할 분리 (`api.js`, `ui.js`, `utils.js`).
2. **BC의 강점**: 중앙 집중식 `STATE` 패턴 적용, 보너스 미션 완수(언어 필터링, Formspree 실제 전송), 체계적인 문서화 및 학습 정리.

두 사람의 강점을 조합하면, **React 학습 시 컴포넌트 설계와 상태 관리를 동시에 가장 빠르게 습득할 수 있는 모범 스터디 커플**이 될 것입니다! 유익하고 즐거운 미팅 되시길 바랍니다! 🎉
