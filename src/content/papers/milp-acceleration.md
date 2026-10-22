---
title: "MILP 솔버는 왜 빨라지는가: 논문으로 읽는 가속 기법"
summary: "MILP 솔버 가속 기법을 논문 단위로 읽은 시리즈의 개요입니다. 각 주제(Presolve, 분지, Conflict, 대칭성, 분해)는 별도 글에서 논문의 예제와 수치로 자세히 다룹니다."
tags: ["MILP", "Branch and Bound", "Solver", "Paper review"]
date: 2026-10-22
slides: "/papers/milp-acceleration.pptx"
part: 0
---

이 글은 시리즈의 개요입니다. 주제마다 논문을 읽고 그 논문의 식, 예제, 실험 수치로 정리한 글을 따로 썼습니다. **슬라이드**는 위의 링크에서 받을 수 있고, 논문의 예제를 더 넣은 [확장판 슬라이드](../milp-acceleration-v2.pptx)도 있습니다.

## 1. 시리즈 목차

| 글 | 읽은 논문 | 한 줄 요약 |
|---|---|---|
| [1. Presolve](../milp-presolve/) | Achterberg, Bixby, Gu, Rothberg, Weninger (Gurobi presolve) | 끄면 시간이 9배 늘고 시간 초과 모델이 488개 늘어난다. redundant 제약, 경계 강화, 계수 강화(Big-M 줄이기), 이중 고정 |
| [2. 분지 규칙](../milp-branching/) | Achterberg, Koch, Martin (2005), Anderson 외 (2020) | 자식의 LP 하한 증가량과 점수 함수(가중합·곱·몫), reliability branching, 점수 함수 비교 실험 설계 |
| [3. Conflict analysis](../milp-conflict-analysis/) | Achterberg (2007) | 실패한 노드의 원인을 쌍대 광선으로 찾아 제약으로 학습한다. feasible 문제에서는 노드 약 50% 감소, 시간 약 15% 증가 |
| [4. 대칭성](../milp-symmetry/) | Presolve 논문 7.1·8.2절 | 대칭 변수 병합과 orbital fixing. 적용되는 모델이 적지만 적용되면 크다 |
| [5. 분해](../milp-decomposition/) | Rahmaniani 외 (2017), Lübbecke & Desrosiers (2005) | Benders와 열 생성. 직접 돌려 본 두 개의 작은 예제 |

## 2. 읽은 범위

전문을 읽은 논문은 6편입니다. 위 글들의 논문에 더해 *MIPLIB 2017*(Gleixner 외)도 읽었습니다. 반대로 **전문을 구하지 못해 읽지 못한 논문이 4편**입니다.

- Margot (2003), *Exploiting orbits in symmetric ILP* — 대칭성 글에서 SCIP 문서와 Presolve 논문의 인용으로만 다뤘습니다.
- Fischetti & Lodi (2003), *Local branching*, 그리고 Danna, Rothberg, Le Pape (2005), *RINS* — 아래 3절에서 초록 수준으로만 다룹니다.
- Achterberg & Wunderling (2013), *Mixed Integer Programming: Analyzing 12 Years of Progress* — 초록만 확인했습니다.

각 글의 "한계" 절에 이 점과 읽은 판본, 제가 직접 계산한 부분을 구분해서 적었습니다.

## 3. 문제와 속도의 구조

혼합정수계획(MILP)은 NP-hard이고 솔버는 분지한계법으로 풉니다. LP 완화로 하한(LB)을, 실행가능해로 상한(UB)을 얻고 간격이 충분히 작아지면 멈춥니다.

$$\text{Gap}=\frac{UB-LB}{|UB|}$$

풀이 시간은 **대략 (탐색 노드 수) × (노드당 LP 비용)** 이라고 보면 이해하기 쉽습니다. 다만 이것은 이해를 돕는 단순화이고 논문의 식이 아닙니다. 실제로는 이전 노드의 해에서 이어서 풀어서 노드마다 비용이 다르고, 절단 평면 생성과 휴리스틱, strong branching의 LP 시간도 들어갑니다. 이 구분으로 정리하면 위 글의 기법들은 다음과 같습니다.

| 줄이는 대상 | 기법 |
|---|---|
| 탐색 노드 수 | 분지 규칙, conflict analysis, 대칭성 처리, 좋은 초기해 |
| LP 하나의 크기와 비용 | presolve(모델 축소와 조임), 강한 정식화, 분해 |

presolve는 모델을 줄이고 조이기 때문에 두 쪽 모두에 영향을 줍니다.

## 4. 해를 빨리 찾는 법 (논문 미확인)

좋은 상한이 있으면 가지치기가 일찍 일어납니다. 대표적인 기법 두 가지의 **전문을 읽지 못했고**, 초록과 솔버 문서 수준으로만 정리합니다.

- **Local branching** (Fischetti & Lodi, 2003): 현재 해 $\bar x$ 주변을 해밍 거리 $k$ 이내로 제한하는 선형 제약을 모델에 더하고, 그 이웃을 MIP 솔버로 탐색합니다. $\bar x$ 에서 1인 변수 집합을 $S$ 라 하면 $\sum_{j\in S}(1-x_j)+\sum_{j\notin S}x_j\le k$ 입니다.
- **RINS** (Danna, Rothberg, Le Pape, 2005): incumbent와 LP 완화해가 같은 값을 갖는 변수를 고정하고, 줄어든 하위 MIP를 푸는 방법입니다. 초록에 따르면 default CPLEX와 local branching보다 어려운 모델에서 낫다고 보고했습니다.

외부에서 만든 해를 넣는 **MIP start**(warm start)도 같은 목적입니다. 간단한 휴리스틱으로 구한 해라도 초기 UB로 쓸모가 있습니다.

## 5. 정식화를 먼저 보세요

논문은 아니지만 실무에서 제일 먼저 확인할 것은 정식화입니다. $x\le My$ 에서 $M$이 크면 LP 완화에서 $y\ge x/M$ 이 0에 가까워져서 완화가 약해집니다. [Presolve 글](../milp-presolve/)에서 논문의 계수 강화 식으로 $M=10$ 이 변수 상한 $u=4$ 로 줄어드는 과정을 풀었고, 이 사이트의 CFLP 프로젝트가 강한 정식화를 비교한 사례입니다. 핵심은 **변수 경계를 정확히 쓰고 Big-M을 데이터로 계산한 가장 작은 값으로** 두는 것입니다.

## 6. 파라미터는 마지막에

아래 표는 **논문이 아니라 솔버 매뉴얼의 지식**이고, 쓰는 버전의 공식 매뉴얼에서 이름과 기본값을 다시 확인해야 합니다.

| 목적 | Gurobi | CPLEX |
|---|---|---|
| 허용 갭 | `MIPGap` (기본 1e-4) | `mip.tolerances.mipgap` |
| 탐색 초점 | `MIPFocus` 1/2/3 | `MIPEMPHASIS` |
| 휴리스틱 | `Heuristics`, `NoRelHeurTime` | `HEURFREQ`, `RINSHEUR` |
| 전처리 | `Presolve` | `PREIND` |
| 자동 튜닝 | `grbtune` | tuning tool |
| 메모리 | `NodefileStart` | `NODEFILEIND` |

## 7. 효과를 어떻게 검증하나

기법의 효과는 문제 구조에 크게 의존합니다. 한 번에 하나만 바꾸고 시간, 갭, 노드 수를 비교해야 합니다.

- **벤치마크**: MIPLIB 2017(Gleixner 외, 2021)은 제출된 5,721개 후보 중 1,065개를 골라 컬렉션으로 만들었고, 솔버 성능 측정용 240개 부분집합(benchmark set)이 따로 있습니다. 선택 과정이 처음으로 데이터 기반으로 수행됐습니다.
- **보고 방식** (Presolve 논문 1.1절): 시간은 shifted geometric mean(shift 1초 등)의 비로 보고하고, 쉬운 문제는 빼서 10초·100초·1,000초 이상 구간으로 나눠 봅니다. 기법이 실제로 작동한 모델만 따로 보는 "영향받은 모델" 열도 둡니다.

## 8. 다음 단계

분지 점수 함수(가중합, 곱, 몫)를 바꿨을 때 SCIP의 성능이 달라지는지 보는 실험을 설계했고 코드를 만들어 두었습니다. 본 실험은 아직 돌리지 않았으며, 결과가 나오면 [분지 규칙 글](../milp-branching/)에 추가하겠습니다.

## 참고문헌

1. Achterberg, T., Wunderling, R. (2013). [Mixed Integer Programming: Analyzing 12 Years of Progress](https://doi.org/10.1007/978-3-642-38189-8_18). *Facets of Combinatorial Optimization*, Springer, 449–481. (전문 미확인)
2. Achterberg, T., Bixby, R., Gu, Z., Rothberg, E., Weninger, D. (2019). [Presolve Reductions in Mixed Integer Programming](https://doi.org/10.1287/ijoc.2018.0857). *INFORMS J. Computing*.
3. Achterberg, T., Koch, T., Martin, A. (2005). [Branching rules revisited](https://doi.org/10.1016/j.orl.2004.04.002). *Oper. Res. Lett.* 33, 42–54.
4. Achterberg, T. (2007). Conflict analysis in mixed integer programming. *Discrete Optimization* 4, 4–20.
5. Margot, F. (2003). Exploiting orbits in symmetric ILP. *Math. Programming* 98, 3–21. (전문 미확인)
6. Fischetti, M., Lodi, A. (2003). [Local branching](https://doi.org/10.1007/s10107-003-0395-5). *Math. Programming* 98, 23–47. (전문 미확인)
7. Danna, E., Rothberg, E., Le Pape, C. (2005). [Exploring relaxation induced neighborhoods to improve MIP solutions](https://doi.org/10.1007/s10107-004-0518-7). *Math. Programming* 102, 71–90. (전문 미확인)
8. Rahmaniani, R., Crainic, T.G., Gendreau, M., Rei, W. (2017). [The Benders decomposition algorithm: A literature review](https://doi.org/10.1016/j.ejor.2016.12.005). *EJOR* 259(3), 801–817.
9. Lübbecke, M., Desrosiers, J. (2005). [Selected topics in column generation](https://doi.org/10.1287/opre.1050.0234). *Oper. Res.* 53(6), 1007–1023.
10. Gleixner, A. et al. (2021). [MIPLIB 2017: data-driven compilation of the 6th mixed-integer programming library](https://doi.org/10.1007/s12532-020-00194-3). *Math. Prog. Comp.* 13(3), 443–490.
11. Anderson, D., Le Bodic, P., Morgan, K. (2020). [Further Results on an Abstract Model for Branching and its Application to Mixed-Integer Programming](https://arxiv.org/abs/1909.01472). arXiv:1909.01472.
