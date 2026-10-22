---
title: "MILP 솔버는 왜 빨라지는가: 논문으로 읽는 가속 기법 9편"
summary: "Presolve, 분지 규칙, 대칭성, 초기해 휴리스틱, 분해까지, 솔버 가속의 수리적 원리를 논문 단위로 정리했습니다."
tags: ["MILP", "Branch and Bound", "Solver", "Paper review"]
date: 2026-10-22
slides: "/papers/milp-acceleration.pptx"
---

## 1. 문제: 왜 느린가

혼합정수계획(MILP)은 다음과 같은 문제입니다.

$$\min\; c^\top x \quad \text{s.t.}\; Ax \le b,\; x_j \in \mathbb{Z}\;(j \in I)$$

이 문제는 NP-hard이고, 솔버는 분지한계법(branch and bound)으로 풉니다. LP 완화로 하한(LB)을, 실행가능해로 상한(UB)을 얻고, 둘 사이의 간격이 충분히 좁아지면 멈춥니다.

$$\text{Gap} = \frac{UB - LB}{|UB|}$$

풀이 시간은 **(탐색 노드 수) × (노드당 LP 비용)** 으로 볼 수 있고, 아래의 모든 기법은 둘 중 하나를 줄입니다. Achterberg & Wunderling(2013)은 CPLEX 12년간의 발전을 구성요소별로 분석해, 개선이 어디서 왔는지 측정하는 방법을 제시했습니다.

## 2. Presolve: 풀기 전에 모델을 줄인다

Achterberg, Bixby, Gu, Rothberg, Weninger(2019)는 Gurobi 구현을 기준으로 presolve 기법을 분류하고 일부 새 기법을 소개합니다. 논문은 presolve가 모델이 "풀 수 없는" 상태와 "풀 수 있는" 상태를 가르기도 한다고 주장합니다.

가장 단순한 예는 활동량(activity) 범위입니다. 변수 경계로 제약 $i$의 좌변이 가질 수 있는 최솟값과 최댓값을 계산합니다.

$$L_i = \min \sum_j a_{ij}x_j, \qquad U_i = \max \sum_j a_{ij}x_j$$

- $U_i \le b_i$ 이면 이 제약은 항상 만족되므로 삭제합니다.
- $L_i > b_i$ 이면 모델이 비실현입니다.

Gurobi에서는 `Presolve=2`가 공격적 모드입니다.

## 3. 분지 규칙: Reliability Branching

어떤 변수를 먼저 분지하느냐가 트리 크기를 크게 좌우합니다. 변수 $j$를 내림/올림했을 때 LP 하한이 오르는 양을 $\Delta_j^-, \Delta_j^+$ 라고 하면 점수는 다음과 같습니다.

$$\text{score}(j) = \max(\Delta_j^-, \varepsilon)\cdot\max(\Delta_j^+, \varepsilon)$$

- **Strong branching**: 후보마다 LP를 실제로 풀어 $\Delta$를 잽니다. 정확하지만 비쌉니다.
- **Pseudocost**: 지금까지 분지한 이력의 평균 증가량으로 $\Delta$를 추정합니다. 싸지만 초기에는 이력이 없어 부정확합니다.

Achterberg, Koch, Martin(2005)의 **reliability branching**은 둘을 섞습니다. 이력이 임계 횟수 $\eta$보다 적은 변수는 strong branching으로 재고, 이력이 쌓이면 pseudocost로 넘어갑니다. IBM 커뮤니티에서는 CPLEX 11 이후의 pseudo cost 규칙이 사실상 이 방식이라고 언급됩니다.

## 4. Conflict Analysis: 실패에서 배운다

Achterberg(2007)는 SAT 솔버의 clause learning을 MIP로 옮겼습니다. 노드가 비실현이면 원인이 된 bound 변경의 집합을 찾아, 같은 조합을 금지하는 제약을 만듭니다. 예를 들어 $x_1=1, x_2=0, x_3=1$ 이 비실현의 원인이면 이진 변수에 대해 다음을 추가합니다.

$$(1-x_1) + x_2 + (1-x_3) \ge 1$$

이진 변수만 있으면 set covering 제약이 되고, 일반 정수 변수가 섞이면 bound disjunction 제약이 됩니다. 비슷한 하위 트리를 다시 탐색하지 않게 해 줍니다.

## 5. 대칭성: 같은 해를 두 번 보지 않는다

동일한 기계나 차량이 여럿이면 "기계 1에 A, 기계 2에 B"와 "기계 1에 B, 기계 2에 A"는 이름만 다른 같은 해입니다. 트리가 이런 중복으로 폭증합니다.

- **모델 수준**: 순서 제약을 직접 추가합니다. 동일 기계라면 $\sum_j x_{j1} \ge \sum_j x_{j2} \ge \cdots$ 처럼 부하의 순서를 강제합니다.
- **솔버 수준**: Margot(2003)은 대칭군의 궤도(orbit)를 이용한 isomorphism pruning과 변수 고정을 제안했고, set covering, covering design, 오류정정 부호에 적용했습니다.

대칭이 거의 없는 모델에서는 이득이 없거나 오히려 손해일 수 있습니다.

## 6. 초기해와 개선 휴리스틱

UB가 좋으면 가지치기가 일찍 일어납니다. 그래서 좋은 해를 빨리 찾는 일이 중요합니다.

**Local branching** (Fischetti & Lodi, 2003). 현재 해 $\bar{x}$ 주변을 해밍 거리 $k$ 이내로 제한하는 제약을 모델에 추가하고, 그 이웃을 MIP 솔버로 탐색합니다. $\bar{x}$에서 1인 변수의 집합을 $S$라 하면 다음과 같습니다.

$$\Delta(x,\bar{x}) = \sum_{j\in S}(1-x_j) + \sum_{j\notin S} x_j \le k$$

**RINS** (Danna, Rothberg, Le Pape, 2005). incumbent $\bar{x}$ 와 LP 완화해 $x^*$ 가 같은 값을 갖는 변수는 두 해가 "합의"한 것으로 보고 고정한 뒤, 줄어든 하위 MIP를 풉니다. 이 기법은 CPLEX 9.0부터 포함되었습니다.

외부에서 만든 해를 주입하는 **MIP start**(warm start)도 같은 목적입니다. 탐욕 알고리즘 같은 간단한 방법으로 얻은 해라도 초기 UB로 쓸모가 있습니다.

## 7. 분해: 큰 문제를 마스터와 부문제로

**Benders 분해**는 변수를 복잡한 쪽($y$)과 쉬운 쪽($x$)으로 나눕니다. 마스터 문제는 부문제에서 얻은 절단(cut)을 하나씩 더해 갑니다.

$$\min\; c^\top y + \eta \quad \text{s.t.}\; \eta \ge u_k^\top (b - By),\;\; 0 \ge v_l^\top (b - By)$$

앞의 부등식이 optimality cut, 뒤의 것이 feasibility cut입니다. Rahmaniani, Crainic, Gendreau, Rei(2017)는 조합최적화 중심으로 Benders의 개선 기법을 분류한 문헌 리뷰입니다.

**열 생성**은 변수 수가 너무 많을 때 일부 열만 둔 축소 마스터를 풀고, 쌍대값 $\pi$ 로 가격 문제를 풀어 개선되는 열만 추가합니다.

$$\min_j\; c_j - \pi^\top a_j < 0 \;\Rightarrow\; \text{열 } j \text{ 추가}$$

Lübbecke & Desrosiers(2005)는 정수계획 관점의 열 생성 리뷰이고, 쌍대 관점을 강조합니다.

## 8. 정식화와 파라미터

논문은 아니지만 실무에서 가장 먼저 확인할 것은 정식화입니다. $x \le M y$ 에서 $M$이 크면 LP 완화에서 $y \ge x/M$ 이 0에 가까워져 완화가 약해집니다. $M$을 데이터에서 계산한 실제 상한으로 줄이고, 필요하면 indicator 제약으로 바꾸고, 계수 단위를 맞춥니다. 이 사이트의 CFLP 프로젝트가 강한 정식화를 비교한 사례입니다.

파라미터는 마지막에 만집니다.

| 목적 | Gurobi | CPLEX |
|---|---|---|
| 허용 갭 | `MIPGap` (기본 1e-4) | `mip.tolerances.mipgap` |
| 탐색 초점 | `MIPFocus` 1/2/3 | `MIPEMPHASIS` |
| 휴리스틱 | `Heuristics`, `NoRelHeurTime` | `HEURFREQ`, `RINSHEUR` |
| 전처리 | `Presolve=2` | `PREIND` |
| 자동 튜닝 | `grbtune` | tuning tool |
| 메모리 | `NodefileStart` | `NODEFILEIND` |

파라미터 이름과 기본값은 쓰는 버전의 공식 매뉴얼에서 다시 확인하세요.

## 9. 효과를 어떻게 검증하나

기법의 효과는 문제 구조에 크게 의존합니다. 한 번에 하나만 바꾸고 시간, 갭, 노드 수를 비교해야 합니다. 표준 벤치마크로는 MIPLIB 2017(Gleixner 외, 2021)이 있습니다. 1,065개 인스턴스가 들어 있고, 솔버 성능 측정용 240개 부분집합이 따로 있습니다.

## 참고문헌

1. Achterberg, T., Wunderling, R. (2013). [Mixed Integer Programming: Analyzing 12 Years of Progress](https://doi.org/10.1007/978-3-642-38189-8_18). *Facets of Combinatorial Optimization*, Springer, 449–481.
2. Achterberg, T., Bixby, R., Gu, Z., Rothberg, E., Weninger, D. (2019). [Presolve Reductions in Mixed Integer Programming](https://doi.org/10.1287/ijoc.2018.0857). *INFORMS J. Computing*.
3. Achterberg, T., Koch, T., Martin, A. (2005). [Branching rules revisited](https://doi.org/10.1016/j.orl.2004.04.002). *Oper. Res. Lett.* 33, 42–54.
4. Achterberg, T. (2007). Conflict analysis in mixed integer programming. *Discrete Optimization* 4, 4–20.
5. Margot, F. (2003). Exploiting orbits in symmetric ILP. *Math. Programming* 98, 3–21.
6. Fischetti, M., Lodi, A. (2003). [Local branching](https://doi.org/10.1007/s10107-003-0395-5). *Math. Programming* 98, 23–47.
7. Danna, E., Rothberg, E., Le Pape, C. (2005). [Exploring relaxation induced neighborhoods to improve MIP solutions](https://doi.org/10.1007/s10107-004-0518-7). *Math. Programming* 102, 71–90.
8. Rahmaniani, R., Crainic, T.G., Gendreau, M., Rei, W. (2017). [The Benders decomposition algorithm: A literature review](https://doi.org/10.1016/j.ejor.2016.12.005). *EJOR* 259(3), 801–817.
9. Lübbecke, M., Desrosiers, J. (2005). [Selected topics in column generation](https://doi.org/10.1287/opre.1050.0234). *Oper. Res.* 53(6), 1007–1023.
10. Gleixner, A. et al. (2021). [MIPLIB 2017: data-driven compilation of the 6th mixed-integer programming library](https://doi.org/10.1007/s12532-020-00194-3). *Math. Prog. Comp.* 13(3), 443–490.
