# AICE Associate 시험 대비 공부 노트

이 파일은 AICE Associate 시험 준비를 위해 유용한 정보 및 환경 설정 내용을 기록하는 곳입니다.

---

## 🛠️ 개발 환경 설정 & `uv` 가상환경

`uv`는 Rust로 작성되어 극도로 빠르고 가벼운 Python 패키지 및 가상환경 관리자입니다. 미니콘다(Conda)처럼 의존성 버전을 자동으로 계산하여 관리해 줍니다.

### 1. 주요 `uv` 명령어
*   **가상환경 생성:** `uv venv`
*   **가상환경 활성화 (macOS/Linux):** `source .venv/bin/activate`
*   **패키지 설치:** `uv pip install <패키지명>`
    *   *예시:* `uv pip install pandas numpy matplotlib seaborn ipykernel`
*   **설치된 패키지 확인:** `uv pip list`

### 2. 현재 구축된 환경 정보
*   **가상환경 경로:** [워크스페이스 디렉토리](file:///Users/f22losophysics1091/Desktop/0625) 내부 `.venv`
*   **Python 버전:** Python 3.12.x
*   **Jupyter 커널명:** `AICE (venv)` (`aice_venv`)
    *   **커널 연결 방법 (VS Code 기준):**
        1. [aice_associate.ipynb](file:///Users/f22losophysics1091/Desktop/0625/aice_associate.ipynb)를 엽니다.
        2. 화면 오른쪽 상단의 **'Select Kernel'**(또는 '커널 선택') 버튼을 클릭합니다.
        3. 목록에서 **'Python Environments...'**를 선택합니다.
        4. 우리가 생성한 가상환경인 **`.venv (Python 3.12.x)`** 또는 등록한 **`AICE (venv)`** 커널을 선택해 줍니다.
        5. *만약 가상환경 목록에 전혀 나타나지 않는다면*, 단축키 `Cmd + Shift + P`를 누르고 `Developer: Reload Window`를 입력하여 에디터를 새로고침(리로드)해 보세요.

### 3. 설치 이슈 해결 기록 (Homebrew vs curl)
*   **Homebrew (`brew`) 란?**
    *   macOS용 오픈소스 패키지 관리자입니다. 터미널에 `brew install <패키지>` 명령어만 입력하면 다양한 개발 도구를 자동으로 내려받아 설치해 주는 편리한 도구입니다.
*   **설치 실패 원인:**
    *   `brew install uv` 실행 시 `/usr/local/Cellar` 등 시스템 디렉토리에 대한 쓰기 권한이 없다는 에러(`not writable`)가 발생하며 실패했습니다.
*   **해결 방식 (curl 우회 설치):**
    *   시스템 전체가 아닌 사용자 개인 홈 폴더(`~/.local/bin`)에만 프로그램을 설치하여 관리자 권한(`sudo`)이 없어도 실행 가능한 방식입니다. `curl` 명령어로 설치 스크립트를 가져와 설치했습니다.
    *   **설치 명령어:**
        ```bash
        curl -LsSf https://astral.sh/uv/install.sh | sh
        ```

---

## 📝 AICE 시험용 손코딩 기본 코드 & 주의점

### 1. 데이터 불러오기 및 인코딩
데이터에 한글이 포함된 경우, `read_csv` 시 인코딩 오류를 방지하기 위해 다음 인코딩 방식을 지정합니다.
```python
import pandas as pd

# Windows 한글 인코딩 (CP949 또는 EUC-KR)
df = pd.read_csv('data.csv', encoding='cp949') 

# 표준 유니코드 (깨질 경우 utf-8 사용)
df = pd.read_csv('data.csv', encoding='utf-8')
```

### 2. 시각화 시 한글 깨짐 방지 (Matplotlib & Seaborn)
차트나 그래프를 그릴 때 한글이 깨지는 현상을 막기 위한 설정입니다.
```python
import matplotlib.pyplot as plt

# Mac OS용 폰트 설정
plt.rc('font', family='AppleGothic') 

# Windows용 폰트 설정 (시험장 환경이 Windows일 경우)
# plt.rc('font', family='Malgun Gothic') 

# 마이너스 기호(-) 깨짐 방지
plt.rcParams['axes.unicode_minus'] = False 
```

---

## 🎯 AICE Associate 시험 수준 및 빈출 유형

AICE Associate는 예제처럼 지문에서 상세 조건을 지정해 주므로 **"자율적인 모델 설계"를 요구하지는 않습니다.** 하지만 실제 시험이 더 어렵게 느껴지는 이유는 **지문에 숨겨진 상세 조건과 실수하기 쉬운 데이터 가공 과정** 때문입니다.

### 1. 난이도가 높게 느껴지는 핵심 포인트 (오답률 높은 곳)
1. **데이터 전처리 (가장 높은 배점)**
   - **결측치(`NaN`) 대체:** 단순 평균이 아닌 최빈값 대체, 혹은 특정 조건에 따라 행을 drop하는 가공.
   - **이상치(`Outlier`) 정제:** IQR(Interquartile Range) 방식을 사용하여 상하한선을 수식으로 구하고 데이터를 필터링하는 문제.
   - **범주형 데이터 인코딩:** 지문에서 요구하는 인코딩 방식(`LabelEncoder` vs `OneHotEncoder`/`pd.get_dummies`)을 명확히 구분하여 적용해야 함.
2. **딥러닝(TensorFlow/Keras) 구현**
   - 머신러닝뿐만 아니라 딥러닝 모델(`Sequential`) 빌드 문제가 필수 출제됩니다.
   - 입력 레이어 크기(`input_shape`), 은닉층 수, 노드 수, 드롭아웃(`Dropout`) 비율, 활성화 함수(`Activation`) 등을 지문 조건에 맞게 정확히 쌓아야 합니다.
3. **평가 지표의 직접 출력**
   - 모델 예측 후 `sklearn.metrics`에서 적절한 평가 지표(MSE, R2-score, F1-score 등)를 불러와 포맷에 맞게 직접 수식으로 처리하여 출력해야 합니다.

### 2. 합격을 위한 준비 전략
*   **라이브러리 패키지 경로 암기 (필수):** 인터넷 검색 및 외부 레퍼런스가 차단된 환경이므로 `sklearn`의 서브패키지 경로(예: `sklearn.model_selection`, `sklearn.preprocessing`, `sklearn.metrics`)를 완벽히 외워야 합니다. Tab 자동완성에 100% 의존하지 않도록 손코딩 훈련을 해야 합니다.
*   **지문 꼼꼼히 해석하기:** "특정 변수를 제외한 훈련 데이터셋 구성", "스케일러를 훈련 세트로만 fit하고 테스트 세트는 transform만 적용" 같은 세부 지시사항을 어기면 결과값이 다 틀어지게 됩니다.

---

## 💡 머신러닝 & 딥러닝 손코딩 흐름 한판 정리 (초심자 필수)

완전히 처음 시작하는 분들을 위한 데이터 로드부터 모델 평가까지의 **표준 6단계 파이프라인** 템플릿입니다. 시험장에 들어가서 이 흐름대로 하나씩 코드를 채워 나가면 됩니다.

### [1단계] 데이터 로딩 및 타겟 분리
```python
import pandas as pd
df = pd.read_csv('data.csv', encoding='cp949')

# X (독립변수: 예측에 쓸 데이터), y (종속변수: 맞추고자 하는 정답) 분리
# 예: 지문에서 'Time_Driving(주행시간)을 예측하라'고 했다면 y가 Time_Driving이 됨.
X = df.drop('Time_Driving', axis=1)
y = df['Time_Driving']
```

### [2단계] 데이터 전처리 (결측치 채우기 & 문자열 변환)
```python
# 결측값(NaN) 채우기 (예: 특정 컬럼의 평균값으로 채우기)
mean_val = X['특정컬럼'].mean()
X['특정컬럼'] = X['특정컬럼'].fillna(mean_val)

# 범주형(문자열) 데이터를 숫자로 인코딩 (One-Hot Encoding)
X = pd.get_dummies(X, columns=['범주형컬럼'], drop_first=True)
```

### [3단계] 학습용 / 검증용 데이터 분할
```python
from sklearn.model_selection import train_test_split

# 데이터를 학습용 80%, 검증용 20% 비율로 분할 (시드 120 고정)
X_train, X_val, y_train, y_val = train_test_split(
    X, y, test_size=0.2, random_state=120
)
```

### [4단계] 데이터 스케일링 (수치 정규화)
```python
from sklearn.preprocessing import MinMaxScaler

scaler = MinMaxScaler()
# 💥 중요: fit_transform은 학습용 데이터(train)에만 적용! 
# 검증용(val) 데이터에는 transform만 적용해야 평가 오염이 없습니다.
X_train_scaled = scaler.fit_transform(X_train)
X_val_scaled = scaler.transform(X_val)
```

### [5단계-A] 머신러닝 모델 학습 및 예측 (scikit-learn)
```python
from sklearn.ensemble import RandomForestRegressor

# 1. 모델 선언 및 파라미터 세팅 (지문 수치 그대로 입력)
rf = RandomForestRegressor(max_depth=5, min_samples_split=3, random_state=120)

# 2. 학습(fit) 및 예측(predict)
rf.fit(X_train_scaled, y_train)
pred = rf.predict(X_val_scaled)
```

### [5단계-B] 딥러닝 모델 학습 및 예측 (TensorFlow/Keras)
```python
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout

# 1. 딥러닝 모델 레이어 쌓기
model = Sequential([
    # 첫 번째 Dense 층에는 입력 피처 개수인 input_shape를 꼭 넣어야 합니다.
    Dense(64, activation='relu', input_shape=(X_train_scaled.shape[1],)),
    Dropout(0.2),
    Dense(32, activation='relu'),
    Dense(1) # 수치 예측(회귀) 모델인 경우 마지막 출력 노드는 1개이며, 활성화 함수는 보통 생략합니다.
])

# 2. 컴파일 (최적화 알고리즘과 오차 평가 방식 정의)
model.compile(optimizer='adam', loss='mse', metrics=['mae'])

# 3. 학습 및 예측
model.fit(X_train_scaled, y_train, epochs=20, batch_size=32, validation_data=(X_val_scaled, y_val))
pred_dl = model.predict(X_val_scaled)
```

### [6단계] 평가 지표 계산 및 출력
```python
from sklearn.metrics import mean_squared_error, r2_score

# 회귀 모델 성능 평가
mse = mean_squared_error(y_val, pred)
r2 = r2_score(y_val, pred)

print(f"MSE: {mse:.4f}")
print(f"R2 Score: {r2:.4f}")
```

---

## 💡 Matplotlib 한글 설정 및 경고 제어 (`warnings`)
데이터 분석 실습 코드 서두에 항상 들어가는 기본 설정 코드들의 역할과 초심자가 주의할 점입니다.

### 1. 한글 깨짐 방지 폰트 지정
```python
import matplotlib.pyplot as plt
plt.rc('font', family='Malgun Gothic') # Windows용 맑은 고딕
# plt.rc('font', family='AppleGothic')  # Mac OS용 애플 고딕
```
*   **역할**: 시각화 라이브러리인 Matplotlib는 기본적으로 영문 폰트만 사용하도록 되어 있어, 차트에 한글이 나타날 때 네모 모양(`□`)으로 글자가 깨지는 현상이 생깁니다. 이를 방지하기 위해 각 OS에 내장된 한글 폰트를 매핑해 주는 코드입니다.
*   **주의**: 본인이 사용 중인 컴퓨터의 OS 환경에 알맞은 폰트를 입력해야 합니다. (맥은 `AppleGothic`, 윈도우는 `Malgun Gothic` 혹은 `NanumGothic`)

### 2. 경고 메시지 무시 (`warnings.filterwarnings('ignore')`)
```python
import warnings
warnings.filterwarnings('ignore')
```
*   **경고(Warning) vs 에러(Error)**:
    *   **에러(Error)**: 문법오류나 데이터 경로 불일치 등으로 인해 **코드가 실행되지 못하고 멈추는 현상**입니다. 무조건 고쳐야 합니다.
    *   **경고(Warning)**: 실행은 정상적으로 완료되지만, "이 방식은 향후 패키지 업데이트 시 지원이 중단될 수 있으니(Deprecated) 새로운 함수를 쓰세요"와 같은 **알림 사항**입니다.
*   **코드 작성 이유**: 머신러닝 라이브러리(pandas, sklearn 등)를 다루다 보면 이러한 권고 메시지가 대량으로 붉은 박스 형태로 출력되어 결과물(표, 그래프 등)을 가려 가독성을 떨어뜨리기 때문입니다. 이를 방지하기 위해 출력을 깨끗하게 정리하려는 의도로 관행적으로 삽입합니다.
*   **초심자 가이드**: 말씀하신 대로 **초심자 단계에서는 이 코드를 주석 처리(앞에 `#` 붙이기)해 두고 모든 경고를 눈으로 확인하는 것이 훨씬 안전**하고 실력 향상에 큰 도움이 됩니다. 코드의 비효율적인 부분이나 향후 변경점을 알 수 있는 피드백이기 때문입니다.
*   **경고를 더 유연하게 다루는 추가 옵션 세 가지**:
    *   **경고 무조건 다 띄우기**: 기본 상태에서도 출력되지 않는 미세한 경고까지 전부 다 화면에 표시하도록 강제합니다.
        ```python
        warnings.filterwarnings('always')
        ```
    *   **경고를 에러(Error)로 올려서 실행 중단하기**: 경고가 발생했을 때 프로그램이 즉각 에러 메시지를 뿜으며 멈추게 만듭니다. 가장 안전하게 버그와 예비적 오류를 잡아내고 싶을 때 활용합니다.
        ```python
        warnings.filterwarnings('error')
        ```
    *   **중복 경고는 딱 한 번만 띄우기**: 반복문 등에서 쏟아지는 동일한 경고 메시지를 처음 1회만 노출시켜 가시성을 지킵니다.
        ```python
        warnings.filterwarnings('once')
        ```

---

## 💡 Pandas 데이터 요약 및 결측치 확인 팁

### 1. 결측치(NaN) 개수만 쏙 골라 출력하는 방법
`df.info()`를 통해서도 전체 행수 대비 덜 채워진 컬럼을 보며 결측치 유무를 유추할 수 있지만, 더 깔끔하게 결측치만 집계하고 싶을 때는 아래 코드를 사용합니다.
*   **전체 컬럼별 결측치 개수 집계**:
    ```python
    df.isnull().sum()
    ```
*   **결측치가 있는(0개 초과) 컬럼만 필터링하여 출력**:
    ```python
    null_counts = df.isnull().sum()
    null_counts[null_counts > 0]
    ```

### 2. `.info()` vs `.info` (괄호의 차이)
*   **`df.info()` (메소드 호출)**: 
    *   괄호 `()`는 **함수나 메소드를 실행(Run)하라는 명령**입니다. 
    *   데이터프레임의 요약 정보를 즉각 출력하는 연산을 수행합니다.
*   **`df.info` (메소드 참조)**:
    *   괄호가 없으면 함수를 실행하는 것이 아니라, **함수 자체를 가리키고 있는 변수명** 역할을 합니다.
    *   실행 결과 대신 `<bound method DataFrame.info of ...>`와 같은 객체 정체성 정보만 텍스트로 보일 뿐 실제 요약 연산은 수행되지 않습니다.
*   **예외: 괄호가 필요 없는 속성(Property)**:
    *   변수처럼 미리 저장된 값을 가져올 때는 괄호를 쓰지 않습니다.
    *   예: 데이터프레임의 크기를 반환하는 `df.shape`, 데이터프레임 각 열의 데이터 타입을 보여주는 `df.dtypes` 등.

---

## 💡 Pandas 결측치(NaN) 대체 방법 (`fillna`)

데이터에 누락된 값(NaN)이 있을 때 특정 값이나 대푯값(평균값, 중앙값 등)으로 채우는 방법입니다.

### 1. 특정 값으로 결측치 채우기
*   **0으로 채우기**:
    ```python
    df['TotalWorkingYears'] = df['TotalWorkingYears'].fillna(0)
    ```

### 2. 대푯값(중앙값, 평균값, 최빈값)으로 결측치 채우기
*   **중앙값(Median)으로 채우기**:
    ```python
    median_income = df['MonthlyIncome'].median()
    df['MonthlyIncome'] = df['MonthlyIncome'].fillna(median_income)
    ```
*   **평균값(Mean)으로 채우기**:
    ```python
    mean_val = df['Age'].mean()
    df['Age'] = df['Age'].fillna(mean_val)
    ```

### ⚠️ 대입 방식과 `inplace=True` 주의점
*   **`inplace=True`를 굳이 안 써도 되는 이유**: 대입 연산자(`=`)를 사용해 `df['컬럼'] = df['컬럼'].fillna(...)` 형태로 작성하면, `inplace` 옵션을 쓰지 않아도 결측치가 깔끔하게 원본에 덮어써집니다.
*   **💥 절대 같이 쓰면 안 되는 치명적 실수**:
    대입 연산(`=`)과 `inplace=True` 옵션을 **동시에 섞어서 쓰면 안 됩니다.**
    ```python
    # ❌ 잘못된 예시: 컬럼 전체가 None으로 변해 데이터가 소실됩니다!
    df['MonthlyIncome'] = df['MonthlyIncome'].fillna(0, inplace=True)
    ```
    *   **이유**: `inplace=True` 옵션을 주는 순간 `fillna` 함수는 아무 데이터도 반환하지 않습니다(즉, 파이썬에서 `None`을 반환). 결과적으로 반환된 `None` 값이 좌변의 `df['MonthlyIncome']`에 대입되면서 **컬럼 전체 데이터가 `None`으로 날아가 버립니다.**

---

## 💡 Pandas 결측치(NaN) 삭제 방법 (`dropna`)

결측치가 포함된 데이터를 대체하지 않고 완전히 지워버리고 싶을 때 사용하는 함수입니다.

### 1. 결측치가 하나라도 있는 행(Row) 삭제
```python
# 결측치가 1개라도 포함된 행은 전부 삭제하여 새로운 df로 저장
df = df.dropna()
```

### 2. 특정 컬럼에 결측치가 있는 행만 삭제 (💥 AICE 시험 단골 유형)
*   "특정 중요 컬럼(예: Attrition)에 결측치가 있는 행만 필터링하여 지우시오"라는 지시사항이 있을 때 사용합니다.
```python
# Attrition 컬럼에 NaN이 있는 행만 골라 삭제
df = df.dropna(subset=['Attrition'])
```

### 3. 결측치가 포함된 열(Column) 삭제
*   행을 삭제하는 것이 아니라, 결측치가 너무 많아 쓸모없는 피처(열) 전체를 날려버릴 때 사용합니다.
```python
# 결측치가 포함된 열 전체를 삭제 (axis=1 사용)
df = df.dropna(axis=1)
```

---

### ⚠️ inplace=True의 동작 원리와 대참사의 정체 (기술 설명)
*   **어떤 데이터가 소실되나요?**: 하드디스크의 원본 CSV 파일이 아니라, **파이썬 메모리 상에 로드되어 실행 중인 데이터프레임(`df`) 객체 내의 해당 열 데이터**가 전부 `None`으로 덮어씌워져 날아갑니다.
*   **작동 메커니즘의 결정적 차이**:
    1.  **대입만 사용 (`df['Col'] = df['Col'].fillna(0)`)**:
        *   우변의 `df['Col'].fillna(0)`이 결측치가 정상적으로 채워진 **새로운 열 객체**를 반환합니다.
        *   대입 기호(`=`)가 메모리에 있는 원본 `df['Col']`을 이 새로운 열 객체로 교체합니다. (안전하게 원하는 결과 획득)
    2.  **대입 + inplace 혼용 (`df['Col'] = df['Col'].fillna(0, inplace=True)`)**:
        *   `fillna(..., inplace=True)`가 메모리 내 원본 `df['Col']` 데이터를 직접 찾아가서 조용히 수정합니다. (여기까진 정상 작동)
        *   그러나 파이썬 규칙상 `inplace=True`가 붙은 함수는 아무런 값도 반환하지 않습니다. (즉, 반환값 = **`None`**)
        *   그다음 대입 기호(`=`)가 동작하면서, 우변의 결과물인 **`None`을 `df['Col']`에 통째로 덮어씌워 버립니다.** 이로 인해 원본 메모리 안의 정상 데이터가 전부 지워지고 `None`만 남게 됩니다.
*   **정리**:
    *   `inplace=True`를 쓸 거라면 대입(`=`)을 쓰지 말고 `df['Col'].fillna(0, inplace=True)` 이렇게 단독으로만 실행해야 합니다.
    *   하지만 판다스에서 `inplace` 옵션 자체가 조만간 지원 중단(Deprecated)될 예정이므로, 평소에 대입 기호(`=`)만 사용하는 습관을 들이는 것이 가장 좋습니다.

### 3. 다른 판다스 주요 함수들의 동일한 원리 (`drop`, `rename` 등)
결측치 대체(`fillna`)뿐만 아니라, 데이터를 변형하거나 행/열을 삭제하는 대부분의 판다스 함수들도 이 원리를 100% 공유합니다. 

*   **행/열 삭제 (`drop`)**:
    *   **대입 방식 (권장)**: `df = df.drop(columns=['Employee_ID'])`
    *   **inplace 방식**: `df.drop(columns=['Employee_ID'], inplace=True)` *(대입 기호 없음)*
*   **컬럼명 변경 (`rename`)**:
    *   **대입 방식 (권장)**: `df = df.rename(columns={'Age': '나이'})`
    *   **inplace 방식**: `df.rename(columns={'Age': '나이'}, inplace=True)` *(대입 기호 없음)*
*   **인덱스 재설정 (`reset_index`)**:
    *   **대입 방식 (권장)**: `df = df.reset_index(drop=True)`
    *   **inplace 방식**: `df.reset_index(drop=True, inplace=True)` *(대입 기호 없음)*

---

## 💡 Pandas 조건부 데이터 필터링 & 이상치 제거

조건에 맞는 데이터를 삭제하거나 특정 데이터만 추출하여 가공하는 방법입니다.

### 1. 불리언 인덱싱 (Boolean Indexing) - 가장 추천
*   **원리**: "특정 기준 이상을 삭제하라"는 말을 **"특정 기준 미만만 살려라"**로 필터링하는 방식입니다.
*   **예시 (MonthlyIncome이 30,000 이상인 이상치 제거)**:
    ```python
    # MonthlyIncome이 30,000 이하인 데이터만 추출하여 df에 덮어쓰기
    df = df[df['MonthlyIncome'] <= 30000]
    ```
    *   *주의*: `df['MonthlyIncome'] = df['MonthlyIncome'] <= 30000` 형태로 작성하면, 열 전체의 수치 데이터가 `True` 또는 `False` 불리언 값으로 치환되어 데이터가 변형되므로 꼭 데이터프레임 전체를 필터링하는 `df = df[조건]` 형태를 유지해야 합니다.
*   **장점**: 코드가 직관적이고 매우 빠릅니다.

### 2. `df.drop()`과 조건 인덱스 추출 활용
*   **원리**: 지우고자 하는 행의 **인덱스 번호(index)** 리스트를 조건식으로 뽑아낸 뒤, 데이터프레임 전체에서 드롭합니다.
*   **예시**:
    ```python
    # 1. 30,000 이상인 행들의 인덱스 추출
    outlier_idx = df[df['MonthlyIncome'] >= 30000].index
    
    # 2. 해당 인덱스 행들 삭제
    df = df.drop(outlier_idx)
    ```
*   **주의**: `df['컬럼'].drop(...)`이 아니라 데이터프레임 객체인 `df.drop(...)`을 써야 행 전체가 제거됩니다.

---

## 💡 컬럼 삭제 및 Seaborn 시각화 (Scatterplot)

### 1. 특정 컬럼(열) 삭제하기 (`drop`)
모델링에 불필요한 고유 ID나 텍스트 열을 삭제할 때는 `drop(columns=[...])`를 사용합니다.
*   **대입 방식 (권장)**:
    ```python
    df = df.drop(columns=['Employee_ID'])
    ```
*   **주의**: `axis=1`을 명시해서 `df = df.drop('Employee_ID', axis=1)`로 작성해도 결과는 같지만, `columns=` 파라미터를 명시하는 것이 직관적입니다.

### 2. Seaborn 산점도 그리기 (`scatterplot`)
두 개의 수치형 변수 관계를 점으로 표현하고, 특정 변수의 범주별로 색상을 다르게 표현(그룹화)할 때 사용합니다.
```python
import seaborn as sns
import matplotlib.pyplot as plt

# x축: 나이(Age), y축: 월소득(MonthlyIncome), 색상구분(hue): 퇴사여부(Attrition)
sns.scatterplot(data=df, x='Age', y='MonthlyIncome', hue='Attrition')

# 시각화 화면 출력
plt.show()
```
*   **AICE 시험 팁**: `hue` 옵션은 특정 범주형 변수의 값에 따라 색깔을 다르게 칠해 데이터를 그룹화하여 보여주는 역할을 합니다. 문제에서 "~~에 따라 색상이 구분되는"이라는 지시가 있으면 100% `hue` 파라미터를 사용하라는 의미입니다.

### 3. 그래프 커스터마이징 기초 (크기 조절 및 한글 제목 지정)
시각화 결과물을 알아보기 편하도록 크기를 조절하거나 한글 제목, 축 이름 등을 설정하는 가장 기본적이고 빈번하게 쓰이는 코드입니다.
```python
# 1. 그래프 크기 조절 (가로 10, 세로 6) - 반드시 sns 함수를 실행하기 전에 설정해야 합니다.
plt.figure(figsize=(10, 6))

# 2. 산점도 생성
sns.scatterplot(data=df, x='Age', y='MonthlyIncome', hue='Attrition')

# 3. 제목 및 축 이름 설정
plt.title('나이와 월소득에 따른 퇴사 여부 분석')
plt.xlabel('나이')
plt.ylabel('월 소득')

plt.show()
```

---

### ⚠️ 컬럼 삭제 (`drop`) 시 재실행 에러 방지 팁
*   **에러 상황**: 주피터 노트북에서 `df = df.drop(columns=['Employee_ID'])`가 포함된 셀을 **한 번 더 실행**하면 `KeyError: "['Employee_ID'] not found in axis"` 에러가 발생합니다.
*   **원인**: 이미 첫 번째 실행 때 컬럼이 정상적으로 지워졌는데, 또 지우려고 하니 판다스가 "해당 컬럼이 존재하지 않는다"고 에러를 내는 것입니다.
*   **해결책 (`errors='ignore'`)**: 
    ```python
    # 컬럼이 있으면 지우고, 없어도 에러 없이 조용히 통과함
    df = df.drop(columns=['Employee_ID'], errors='ignore')
    ```
    *   AICE 시험이나 평소 실습 시 셀을 반복해서 실행할 일이 많으므로, 이 옵션을 붙여두면 재실행 시 오류가 나는 번거로움을 원천 차단할 수 있어 매우 유용합니다.

*   **여러 컬럼 한꺼번에 삭제하기**:
    지워야 할 컬럼이 여러 개인 경우, 리스트 안에 쉼표로 컬럼명을 나열하여 전달하면 한 번에 지워집니다.
    ```python
    # Employee_ID와 Gender 컬럼을 한꺼번에 제거 (재실행 에러 방지 포함)
    df = df.drop(columns=['Employee_ID', 'Gender'], errors='ignore')
    ```

---

## 💡 AICE Associate 중/후반부 핵심 패키지 & 모델링 팁

### 1. 데이터 스케일링 (`StandardScaler`)
*   **역할**: 데이터의 평균을 0, 분산을 1이 되도록 변환하여 수치형 변수 간의 단위 편차를 제거합니다.
*   **주의**: 원-핫 인코딩으로 변환된 더미 변수(0 또는 1)에는 표준화를 굳이 적용하지 않으며, 순수 숫자형 컬럼(`Age`, `MonthlyIncome` 등)에만 적용하는 것이 정석입니다.
```python
from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
# 수치형 변수들만 피팅 및 변환
X_train[num_cols] = scaler.fit_transform(X_train[num_cols])
```

### 2. XGBoost 모델 구축 (`XGBClassifier`)
*   정형 데이터 분류 성능이 매우 우수하여 AICE Associate 시험 모델링 단계에 가장 단골로 나오는 머신러닝 모델 중 하나입니다.
```python
from xgboost import XGBClassifier
# n_estimators(생성할 트리 개수), learning_rate(학습률) 하이퍼파라미터 세팅
xgb = XGBClassifier(n_estimators=100, learning_rate=0.1, random_state=120)
xgb.fit(X_train, y_train)
```

### 3. 딥러닝 조기 종료 제어 (`EarlyStopping`)
*   **역할**: 딥러닝 학습 시 지정한 에포크(epochs)를 전부 돌기 전에 **검증 데이터의 손실(`val_loss`)이 일정 횟수 이상 더 나아지지 않으면 과적합(Overfitting)을 예방하기 위해 스스로 학습을 중단**하는 기능입니다.
```python
from tensorflow.keras.callbacks import EarlyStopping
# patience=5 (5회 동안 개선이 안 되면 조기 종료), restore_best_weights=True (최적 오차 시점 가중치 복원)
es = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)
history = model.fit(X_train, y_train, epochs=50, callbacks=[es], validation_data=(X_test, y_test))
```

### 4. 혼동 행렬(Confusion Matrix)과 재현율(Recall)
*   **재현율(Recall)**: **실제 퇴사자(1) 중 모델이 정확히 퇴사자(1)로 감지하고 잡아낸 비율**입니다.
*   **비즈니스 관점의 팁**: 직원 이탈 방지 태스크에서는 '퇴사 안 할 사람을 오인해서 면담하는 것(Precision 실수)'보다, **'퇴사할 직원을 감지하지 못하고 그냥 놓쳐서 퇴사하게 놔두는 것(Recall 실수)'이 훨씬 뼈아픕니다.** 따라서 AICE 시험에서도 재현율(Recall) 지표가 모델의 실제 채택 기준에서 크게 중요하게 다루어집니다.

---

## 💡 Pandas 다중 조건 필터링 (AND / OR)

조건을 만족하는 행만 남길 때, 조건이 여러 개인 경우의 결합 방법입니다.

### 1. AND 조건 (`&`) - '이면서 / 동시에'
*   **조건**: 나열된 모든 조건을 동시에 만족하는 행만 남깁니다.
*   **💥 필수 주의**: 각 조건식을 반드시 **소괄호 `()`**로 감싸주어야만 파이썬 연산자 우선순위 에러가 발생하지 않습니다.
```python
# MonthlyIncome이 10,000 이상이면서 동시에 30,000 이하인 행만 남기기
df = df[(df['MonthlyIncome'] >= 10000) & (df['MonthlyIncome'] <= 30000)]
```

### 2. OR 조건 (`|`) - '이거나 / 또는'
*   **조건**: 조건들 중 어느 하나라도 만족하는 행을 남깁니다.
```python
# 부서가 'Sales'이거나 'R&D'인 행만 남기기
df = df[(df['Department'] == 'Sales') | (df['Department'] == 'R&D')]
```

---

## 💡 Pandas 오타로 인한 신규 컬럼 생성 주의보
*   **상황**: 기존 컬럼의 값을 교체하려고 대입(`=`)을 했는데, 의도와 다르게 데이터프레임에 컬럼이 중복되어 늘어나는 현상입니다.
*   **원인**: 좌변에 입력한 컬럼명에 미세한 오타(예: `MonthlyIncome` 대신 `MonthlyIncom`)가 있을 경우, 판다스는 에러를 내지 않고 **해당 오타명으로 새로운 열(Column)을 새로 생성해서 대입**해 버립니다.
*   **해결책**:
    1.  잘못 생성된 오타 열을 즉시 제거합니다:
        ```python
        df = df.drop(columns=['MonthlyIncom'], errors='ignore')
        ```
    2.  또는 주피터 노트북의 코드를 수정한 후 **Kernel -> Restart & Run All**을 통해 데이터를 처음부터 깨끗하게 다시 로드하고 실행해 줍니다. (가장 확실함)









