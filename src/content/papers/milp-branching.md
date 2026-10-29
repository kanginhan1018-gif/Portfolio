---
title: "분지 규칙: 어떤 변수를 먼저 쪼갤까"
summary: "Reliability branching 논문(Achterberg, Koch, Martin 2005)을 읽고, 자식 노드의 LP 하한 증가량과 점수 함수(가중합, 곱, 몫)를 정리하고 점수 함수 비교 실험을 설계했습니다."
tags: ["MILP", "Branch and Bound", "Branching", "Paper review"]
date: 2026-10-22
part: 2
---

이 글은 Achterberg, Koch, Martin의 *Branching Rules Revisited* (ZIB Report 04-13, Operations Research Letters 33, 2005) 전문을 읽고 정리한 것입니다. 점수 함수의 후속 연구는 Anderson, Le Bodic, Morgan의 *Further Results on an Abstract Model for Branching* (arXiv 1909.01472) 전문과 SCIP 소스 코드(`branch.c`)로 확인했습니다. 제가 만든 숫자 예시에는 그렇게 표시했습니다.

## 1. 분지한계법에서 분지가 하는 일

논문의 Algorithm 1을 최소화 문제로 옮기면 다음과 같습니다.

1. 문제 집합 $S$를 LP 완화 $P_{LP}$로 시작합니다.
2. $S$가 비면 최적값 $c^*$를 반환합니다.
3. 문제 $Q\in S$를 하나 꺼냅니다.
4. LP $\bar c_Q=\min\{c^\top x\mid x\in Q\}$ 를 풉니다. 최적해는 $\bar x_Q$ 입니다.
5. $\bar c_Q \ge c^*$ 이면 버리고 2로 갑니다.
6. $\bar x_Q$가 정수 실행가능하면 $c^*:=\bar c_Q$ 로 갱신하고 2로 갑니다.
7. 아니면 **분지**해서 $Q$를 부분 문제로 쪼개 $S$에 넣고 3으로 갑니다.

분지는 LP 완화를 계속 유지하기 위해 **선형 부등식**으로만 합니다. 가장 흔한 것은 변수 하나의 구간을 쪼개는 것입니다. 정수 변수 $i$의 LP 값 $\bar x_i$ 가 분수일 때

$$f_i^-=\bar x_i-\lfloor\bar x_i\rfloor,\qquad f_i^+=\lceil\bar x_i\rceil-\bar x_i$$

로 두고, 왼쪽 자식 $Q_i^-$ 에는 $x_i\le\lfloor\bar x_i\rfloor$, 오른쪽 자식 $Q_i^+$ 에는 $x_i\ge\lceil\bar x_i\rceil$ 를 추가합니다. 논문은 더 복잡한 부등식이나 세 갈래 이상 분지는 범용 솔버에서 드물게 쓰인다고 말합니다.

**변수 선택(Algorithm 2)** 은 세 단계입니다. 분수 변수의 집합 $C$를 만들고, 후보마다 점수 $s_i$ 를 계산하고, 점수가 가장 큰 변수를 고릅니다. 규칙들의 차이는 2단계의 점수 계산뿐입니다.

## 2. 점수의 재료: 자식 노드의 LP 하한 증가량

후보 $i$를 분지했을 때 두 자식의 **LP 하한 증가량**은 다음과 같이 정의됩니다.

$$\Delta_i^-=\bar c_{Q_i^-}-\bar c_Q,\qquad \Delta_i^+=\bar c_{Q_i^+}-\bar c_Q$$

이것은 정수 조건을 추가한 것이 아닙니다. **부모 LP에 변수 하나의 경계 제약만 더해 다시 풀었을 때 LP 최적값이 얼마나 올랐는가**입니다. 자식에서도 다른 변수의 정수 조건은 계속 완화돼 있습니다. 경계 하나가 추가되면 실행가능 영역이 줄어서 LP 최적값(최소화)은 같거나 커지고, 이 증가량이 하한의 진전입니다. 한 자식이 비실현이면 증가량은 사실상 무한이고, 논문은 이 경우 "특별한 처리가 필요하다"고만 적습니다.

**직접 만든 숫자 예.** 부모 LP 값이 10이고 $\bar x_i=2.4$ 입니다. 왼쪽 자식($x_i\le2$)의 LP 값이 10.8, 오른쪽 자식($x_i\ge3$)이 11.5라면 $\Delta^-=0.8$, $\Delta^+=1.5$ 입니다. $f^-=0.4$, $f^+=0.6$ 이므로 단위 변화당 이득은 $0.8/0.4=2$, $1.5/0.6=2.5$ 입니다.

## 3. 두 증가량을 하나의 점수로: 가중합, 곱, 몫

규칙들은 $(\Delta^-,\Delta^+)$ 를 점수 하나로 합쳐야 합니다. 이 글에서 가장 헷갈리기 쉬운 부분이라 따로 정리합니다.

### 이 논문의 점수 (식 3)

$$\mathrm{score}(q^-,q^+)=(1-\mu)\min\{q^-,q^+\}+\mu\max\{q^-,q^+\},\qquad \mu=1/6$$

작은 쪽에 5/6, 큰 쪽에 1/6의 가중치를 주는 **가중합**입니다. 논문은 $\mu$가 "보통 경험적으로 정한 상수이고, 때로는 실행 중에 조정한다"고 하며, 자기들의 솔버(SIP)에서는 $1/6$ 을 썼습니다.

### 현재 SCIP의 점수

SCIP 소스(`SCIPbranchGetScore`)와 파라미터 문서(`branching/scorefunc`, `branching/scorefac`)로 확인한 세 가지 선택지입니다. $d,u$는 아래·위 증가량이고 아주 작은 $\varepsilon$ 이하로는 내려가지 않게 바닥을 둡니다.

| `scorefunc` | 이름 | 식 |
|---|---|---|
| `s` | 가중합 | $\mathrm{scorefac}\cdot\max(d,u)+(1-\mathrm{scorefac})\cdot\min(d,u)$ |
| `p` (**기본값**) | 곱 | $d\cdot u$ |
| `q` | 몫 | $\min(d,u)^2/\max(d,u)$ |

`scorefac` 기본값은 0.167입니다. 즉 2005년 논문의 식은 SCIP의 `s`에 `scorefac=1/6`을 넣은 것과 같은 형태이고, 지금의 SCIP는 기본으로 곱을 씁니다.

### 곱이 가중합보다 나은가

Anderson 외는 SCIP의 기본 점수가 곱이라고 설명하면서, Achterberg의 박사학위 논문이 "곱이 이전의 표준이던 가중합보다 실험에서 10% 넘게 낫다"는 것을 보였다고 인용합니다. 저는 박사학위 논문 원문은 읽지 못했고 이 인용만 확인했습니다.

### 더 나아간 점수: ratio와 svts

Le Bodic–Nemhauser의 추상 모델에서 나온 점수들입니다. 변수 $(l,r)$ 하나만 계속 분지했을 때 트리 크기의 점근 성장률 $\varphi$ 는 다항식 $x^r-x^{r-l}-1$ 의 1보다 큰 유일한 실근입니다. 이 값이 작을수록 트리가 천천히 커집니다.

- **ratio 규칙**: 트리 높이를 $\lfloor G/l\rfloor$ 로 추정해 10보다 크면 $\varphi$ 로 점수를 매기고, 아니면 곱을 씁니다($G$는 닫아야 할 갭).
- **svts 규칙**: 변수 하나로 만든 트리의 크기 $t(G)$ 로 점수를 매깁니다.

Anderson 외가 SCIP 6.0에 구현해 MIPLIB 2017 benchmark set에서 곱(기준) 대비 비교한 결과입니다(시간 기하평균의 비, 1보다 작으면 빠름).

| 인스턴스 | ratio | svts |
|---|---|---|
| benchmark 전체 | 1.01 (1% 느림) | 0.99 (1% 빠름) |
| 어떤 설정에서든 10,000 노드 이상 필요 | 0.99 | 0.93 |
| 50,000 노드 이상 필요 | 0.96 | 0.89 |

큰 트리가 필요한 문제에서만 눈에 띄고, 전체로는 거의 차이가 없습니다. 이 둘은 SCIP 10.0의 `scorefunc` 파라미터에는 없습니다.

### 가중합과 곱은 언제 다른 후보를 고르나

**직접 만든 숫자 예.** 후보 A의 증가량이 $(0.01,\ 100)$, 후보 B가 $(2,\ 2)$ 입니다.

| 후보 | 가중합 ($\mu=1/6$) | 곱 |
|---|---|---|
| A (0.01, 100) | 16.7 | 1.0 |
| B (2, 2) | 2.0 | 4.0 |

가중합은 한쪽만 크게 오르는 A를, 곱은 두 자식이 고르게 오르는 B를 고릅니다. 곱은 한쪽이 0에 가까우면 점수가 거의 0이 됩니다. 어느 쪽이 실제로 트리를 작게 만드는지는 문제에 따라 다릅니다.

### "비율로 정규화해서 더하면?"에 대하여

두 가지로 나누어 볼 수 있습니다.

- **공통 값으로 나눈 비율의 합**은 같은 노드에서 모든 후보에 같은 분모를 쓰므로 **순위가 바뀌지 않습니다.** 결국 단순 합 $\Delta^-+\Delta^+$ 이고, 논문 식에서 $\mu=1/2$ 인 경우입니다.
- **후보마다 다른 값으로 나눈 비율**(예: $\Delta/f$)은 이미 pseudocost가 쓰는 단위당 이득입니다(아래 4절).
- 방향별로 **그 방향의 최대 증가량으로 나눠서 더하는** 규칙(`normsum`)은 순위를 바꿉니다. 제가 이 대화에서 생각해 본 한 가지 해석이고 출판된 규칙이 아닙니다. 아래 실험의 탐색적 가설입니다.

## 4. 규칙들

### 4.1 가장 분수에 가까운 변수 (most infeasible)

$s_i=0.5-|\bar x_i-\lfloor\bar x_i\rfloor-0.5|$. 분수 부분이 0.5에 가장 가까운 변수를 고릅니다. 위로 올릴지 아래로 내릴지 가장 판단하기 어려운 변수라는 직관입니다. 논문의 실험에서는 **random 선택과 거의 같은 성능**이라, "쓸모없다"고 결론짓고 이후 비교에서 뺍니다.

### 4.2 Pseudocost

과거 분지의 성공을 기록해서 $\Delta$ 를 추정합니다. 변수 $i$를 위로 분지한 문제 $Q^+$ 를 풀어서 실행가능했을 때, 단위 변화당 이득과 그 평균은 다음과 같습니다.

$$\varsigma_i^{+}=\Delta_i^{+}/f_i^{+},\qquad \Psi_i^{+}=\sigma_i^{+}/\eta_i^{+}$$

$\sigma_i^+$ 는 $\varsigma_i^+$ 의 누적 합, $\eta_i^+$ 는 그 횟수입니다. 아래 방향도 같습니다. 점수는 추정한 증가량으로 계산합니다.

$$s_i=\mathrm{score}\big(f_i^{-}\Psi_i^{-},\ f_i^{+}\Psi_i^{+}\big)$$

처음에는 기록이 없어서 $\eta=0$ 입니다. 이런 pseudocost를 "초기화되지 않았다"고 하고, 초기화된 값들의 평균 $\Psi_{avg}$ 로 대신합니다. 모두 초기화되지 않았으면 1로 둡니다. 약점은 트리 윗부분에서 기록이 없는 채로 가장 중요한 결정을 내린다는 점입니다.

### 4.3 Strong branching

분지하기 **전에** 후보마다 두 자식 LP를 실제로 풀어서 $\Delta$ 를 측정합니다(CPLEX 7.5에서 도입). 후보 전체를 LP 끝까지 풀면 **full strong branching**입니다. 지역적으로 가장 좋은 변수를 고르기 때문에 노드 수가 가장 적게 나오는 경향이 있지만, 노드당 시간이 큽니다. 속도를 내는 방법은 세 가지입니다.

- 후보 집합 $C'\subseteq C$ 로 제한
- 후보당 쌍대 심플렉스 반복 수를 $\gamma$ 로 제한(논문의 SIP에서는 $\gamma=2\bar\gamma$, $\bar\gamma$ 는 지금까지 LP당 평균 반복 수)
- **look-ahead $\lambda$**: 후보를 pseudocost 점수가 큰 순서로 평가하다가 새 최고 후보가 $\lambda$번 연속 나오지 않으면 중단

### 4.4 Hybrid strong/pseudocost

깊이 $d$ 이하의 윗부분에서는 strong branching, 그 아래에서는 pseudocost를 씁니다. 약점은 깊이가 **고정**이라 트리 모양을 모른다는 점입니다.

### 4.5 Strong branching으로 초기화한 pseudocost

pseudocost가 초기화되지 않은 변수에만 strong branching을 하고, 그 결과로 pseudocost를 초기화합니다.

### 4.6 Reliability branching (이 논문의 제안)

4.5를 일반화합니다. 초기화되지 않은 변수뿐 아니라 **믿기 어려운** 변수에도 strong branching을 씁니다. pseudocost가 믿기 어렵다는 것은

$$\min\{\eta_i^-,\eta_i^+\}<\eta_{rel}$$

일 때입니다. Algorithm 3의 흐름은 이렇습니다.

1. 모든 후보의 점수를 pseudocost로 계산해서 큰 순서로 정렬합니다.
2. 믿기 어려운 후보에 대해 (a) 두 자식에서 쌍대 심플렉스를 최대 $\gamma$ 번 돌려 증가량 $\tilde\Delta^\pm$ 를 얻고, (b) 그 값으로 pseudocost를 갱신하고, (c) 점수를 $\mathrm{score}(\tilde\Delta^-,\tilde\Delta^+)$ 로 바꿉니다.
3. 최고 점수가 $\lambda$번 연속 안 바뀌면 중단합니다.

### 파라미터로 보면 모든 규칙이 한 줄로 이어집니다 (Figure 1)

| 설정 | 결과 |
|---|---|
| $\eta_{rel}=0$ (또는 hybrid의 $d=0$) | 순수 pseudocost |
| $\eta_{rel}=1$ | strong branching으로 초기화한 pseudocost |
| $\eta_{rel},d\to\infty$ | strong branching |
| 위에 더해 $\lambda=\infty$ | full strong branching |

가장 좋은 성능은 $\eta_{rel}\in[4,8]$ 구간에서 나옵니다.

## 5. 논문의 실험

- **인스턴스.** MIPLIB 2003과 다른 문헌의 인스턴스 중 CPLEX 9.0이 5,000 노드 이상, 1시간 이하로 푸는 것만 골랐습니다.
- **환경.** 833 MHz Alpha 21264 워크스테이션, 시간 제한 1시간. 자기들의 solver SIP에 구현했습니다.
- **지표.** 총합과 기하평균(geometric mean)을 보고, 결론은 기하평균에 근거합니다.

### Table 1 요약 (기하평균, lookahead $\lambda=4$)

| 규칙 | 노드 수 | 시간(초) | 못 푼 인스턴스 |
|---|---|---|---|
| random | 275,789 | 923.6 | 11 |
| most infeasible | 262,369 | 938.0 | 11 |
| pseudocost | 88,707 | 283.4 | 2 |
| full strong | 7,242 | 504.4 | 2 |
| hybrid, 깊이 10 | 65,966 | 229.6 | 2 |
| reliability, $\eta_{rel}=1$ | 70,014 | 216.4 | 1 |
| reliability, $\eta_{rel}=4$ | 53,523 | 178.2 | 0 |
| **reliability, $\eta_{rel}=8$** | 48,773 | **170.5** | 0 |
| reliability, $\eta_{rel}=16$ | 44,650 | 179.0 | 0 |
| reliability, $\eta_{rel}=32$ | 39,655 | 184.2 | 0 |

### 논문의 결론 (3.3절)

1. **full strong branching은 노드 수가 가장 적지만 시간은 그렇지 않습니다.** 노드 수 7,242(기하평균)는 reliability(8)의 48,773보다 훨씬 작지만, 시간은 504.4초 대 170.5초입니다. 참고로 strong branching 계열은 자식이 비실현이거나 상한을 넘으면 그 자식을 노드로 만들지 않아서, 마지막 잎 노드가 세어지지 않아 노드 수가 약 절반으로 잡힌다는 주석이 논문에 붙어 있습니다.
2. **시간 기준으로 reliability branching은 어떤 파라미터에서도 hybrid보다 낫습니다.** hybrid는 깊이를 고정하는데, neos3 같은 문제의 트리는 경로처럼 길게 뻗고(한 변수를 1로 고정하면 두세 개 고정 뒤 거의 항상 비실현), 평균 깊이가 깊어서 strong branching이 거의 쓰이지 않습니다. 반대로 vpm2는 균형 잡힌 트리입니다.
3. **look-ahead는 일정 값 이상에서 노드 수에 큰 영향이 없고**, 값이 커지면 노드당 시간만 늘어납니다. 후보가 이미 pseudocost 순으로 정렬돼 있어 $\lambda=4$ 로도 대부분 최고 후보를 찾습니다.
4. **$\eta_{rel}$ 를 키우면 노드 수는 줄지만 시간은 $\eta_{rel}=8$ 까지 좋아지다가 다시 나빠집니다.** $(\eta_{rel}=8,\ \lambda=4)$ 가 새로운 최적점입니다.

저자들은 마지막으로 full strong branching과의 노드 수 격차가 남아 있고, 노드당 시간을 크게 늘리지 않고 이 격차를 줄일 수 있느냐가 남은 질문이라고 씁니다.

### $\eta_{rel}=4\sim8$ 은 증명된 값인가

아닙니다. 위 결과는 인스턴스 집합에서 측정한 경험적 최적점이고, "관측이 몇 번이면 pseudocost가 믿을 만해진다"를 보인 이론은 제가 찾은 범위에서는 없었습니다. 대신 이 고정 횟수 기준 자체를 문제 삼은 후속 연구가 있습니다.

Hendel (2015)은 고정 횟수 문턱값의 약점을 두 가지로 지적합니다. 구조가 다른 변수들에 같은 횟수를 요구한다는 점, 문제 크기가 커질 때 같은 값이 잘 맞는지 알 수 없다는 점입니다. 대안으로 변수별 pseudocost 관측값의 표본 분산을 써서 두 가지 기준을 제안합니다.

- **상대오차 기준(rer):** pseudocost 신뢰구간의 상대오차가 기준 이하가 되면 믿을 만하다고 봅니다.
- **가설검정 기준(hyp):** 현재 최고 후보를 이길 가능성이 낮은 후보를 Student t-검정으로 걸러냅니다.

SCIP 3.1.0.2에서 MIPLIB 3.0/2003/2010의 135개 인스턴스(제한시간 2시간)로 고정 문턱값 5와 비교한 결과입니다.

| 설정 | 노드 수(기하평균, 기준=100%) | 시간 |
|---|---|---|
| 고정 5 (기준) | 100% | 기준 |
| rer-0.01 | 80.5% | 기준보다 6.1% 느림 |
| hyp | 82.4% | 거의 같음(+1.5%) |

(98개 인스턴스를 모든 설정이 푼 경우의 값입니다.) 노드 수는 줄었지만 시간은 줄지 않았습니다. 새 기준이 strong branching을 더 많이 쓰기 때문이라고 논문이 설명합니다. 그래서 "고정 횟수 대신 통계 기준이 낫다"고 단정할 결과는 아닙니다. 논문 스스로도 첫 구현일 뿐이고, 고정 문턱값을 strong branching 비용에 따라 동적으로 조정하면 성능이 좋아진다고 덧붙입니다.

이 논문에서 확인한 점이 하나 더 있습니다. 2005년 논문의 8은 SCIP 3.1 시점에 5로 바뀌어 있었습니다. 위 기본값 표의 `maxreliable=5.0`과 같은 값이고, 동적 조정 폭이 `minreliable`과 `maxreliable`로 나뉘어 있으리라 짐작하지만 소스에서 확인하지는 않았습니다.

Le Bodic과 Nemhauser의 추상 모델은 위에서 다룬 점수 함수(곱 대 몫)의 이론이고, 신뢰도 문턱값은 다루지 않습니다.

### 지금의 SCIP는 어떻게 설정돼 있나

PySCIPOpt 6.3.0(SCIP 10.0)에서 읽은 기본값입니다.

| 파라미터 | 값 |
|---|---|
| `branching/scorefunc` | `p` (곱) |
| `branching/scorefac` | 0.167 |
| `branching/relpscost/minreliable` | 1.0 |
| `branching/relpscost/maxreliable` | 5.0 |
| `branching/relpscost/maxlookahead` | 9 |

2005년 논문의 최적점($\eta_{rel}=8$, $\lambda=4$)과 지금의 기본값은 다릅니다. 신뢰도 기준이 `minreliable`, `maxreliable` 두 값으로 나뉘어 있는데, 이 값들이 정확히 어떻게 쓰이는지는 확인하지 못했습니다.

## 6. 직접 해 보려는 실험

점수 함수 하나만 바꿔서 SCIP의 성능이 달라지는지 보는 실험을 설계하고 코드를 만들어 두었습니다. 아직 본 실험은 돌리지 않았고, 아래는 계획입니다.

- **1단계**: SCIP 자신의 reliability pseudocost 분지에서 `scorefunc`/`scorefac` 만 바꿉니다. 비교 대상은 곱(기본값), 가중합($1/6$), 단순 합($1/2$), 몫입니다.
- **2단계**: 후보 10개를 strong branching으로 평가하고 점수를 직접 계산하는 규칙을 PySCIPOpt의 분지 규칙으로 구현했습니다. pseudocost 추정 오차를 빼고 점수 함수의 효과만 보기 위한 것입니다. 여기에 위의 `normsum`이 들어갑니다.
- **인스턴스**: MIPLIB 2017 benchmark set 240개에서 기본 설정으로 10~300초에 풀리는 것만 고릅니다. 시드 3개, 시간 제한 600초입니다.
- **지표**: 푼 개수와 시간·노드 수의 shifted geometric mean(시간 shift 10, 노드 shift 100)을 기준선(곱) 대비 비율로 봅니다. 어려운 하위 집합(10,000 노드 이상)도 따로 봅니다.
- **가설**: H1 곱이 가중합(1/6)보다 노드가 적다. H2 단순 합은 곱보다 나쁘다. H3 몫은 곱과 비슷하다. 탐색적으로 `normsum`은 단순 합과 곱 사이에 있을 것이다. 결과가 이 가설과 달라도 그대로 보고합니다.

## 7. 한계

- 2005년 논문은 한 솔버(SIP)와 당시 하드웨어(833 MHz)에서의 결과입니다. 지금의 솔버와 기본값은 다릅니다.
- ratio, svts의 수치는 Anderson 외가 SCIP 6.0에서 낸 것이고, 이 글에서 재현하지 않았습니다.
- $\eta_{rel}$ 의 최적 구간(4~8)은 경험적 결과이고, 이를 증명한 연구는 찾지 못했습니다. Achterberg의 박사학위 논문(2007)은 열어 보지 못했습니다. Hendel (2015)은 PDF 본문에서 확인했습니다.
- 곱이 가중합보다 10% 넘게 낫다는 주장은 박사학위 논문을 직접 읽지 못하고 인용으로만 확인했습니다.

이전 글: [Presolve](../milp-presolve/) · 다음 글: [Conflict analysis](../milp-conflict-analysis/) · 전체 개요: [MILP 솔버는 왜 빨라지는가](../milp-acceleration/)

## 참고문헌

- Achterberg, T., Koch, T., Martin, A. (2005). [Branching rules revisited](https://doi.org/10.1016/j.orl.2004.04.002). *Oper. Res. Lett.* 33, 42–54.
- Anderson, D., Le Bodic, P., Morgan, K. (2020). [Further Results on an Abstract Model for Branching and its Application to Mixed-Integer Programming](https://arxiv.org/abs/1909.01472). arXiv:1909.01472.
- Hendel, G. (2015). [Enhancing MIP Branching Decisions by Using the Sample Variance of Pseudo Costs](https://opus4.kobv.de/opus4-zib/frontdoor/index/index/docId/5459). *CPAIOR 2015*, LNCS 9075, 199–214 (ZIB Report 15-28).
- SCIP 소스 코드 `src/scip/branch.c` (`SCIPbranchGetScore`)와 [SCIP 파라미터 목록](https://www.scipopt.org/doc/html/PARAMETERS.php).
