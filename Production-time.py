from ortools.linear_solver import pywraplp
import matplotlib.pyplot as plt
# 1. OR-Tools solver 생성
solver = pywraplp.Solver.CreateSolver('SCIP')

#Big-M
M = 100000

# 제품
products = ['P1', 'P2', 'P3', 'P4', 'P5']

#납기일
due = {
    'P1': 3,
    'P2': 1,
    'P3': 2,
    'P4': 5,
    'P5': 0
}


# 원자재 수
materials = ['R1', 'R2', 'R3']

# 원자재 조달기간
lt = {
    'R1': 5,
    'R2': 10,
    'R3': 1
}

# 빠른 조달 리드타임 및 조달 가능량 정의
transit = {
    'R1': {'lt': 2, 'qty': 30},
    'R2': {'lt': 3, 'qty': 30},
    'R3': {'lt': 0, 'qty': 30},
}

# 각 제품별 원자재 리스트에 없는 원자재는 0으로 설정
for material in materials:
    if material not in transit:
        transit[material]['lt'] = 0
        transit[material]['qty'] = 0



# 원자재 재고
inventory = {
    'R1': 0,
    'R2': 0,
    'R3': 0,
}

# 제품별 원자재 소요량
requirements = {
    'P1': {'R1': 10, 'R2': 5},
    'P2': {'R1': 20, 'R3': 10},
    'P3': {'R2': 15, 'R3': 5},
    'P4': {'R1': 5, 'R2': 5, 'R3': 5},
    'P5': {'R3': 20},
}

# 각 제품별 원자재 리스트에 없는 원자재는 0으로 설정
for product in requirements:
    for material in materials:
        if material not in requirements[product]:
            requirements[product][material] = 0

#각 제품별 원자재 조달 전 생산 가능여부
PrePro = {i:{j: solver.IntVar(0, 1, f'PrePro_{i}_{j}') for j in materials} for i in products}

#제품별 생산시작시간
st = {i: solver.IntVar(0, solver.infinity(), f'st_{i}') for i in products}

#제품별 납기지연시간
Tardiness = {i: solver.IntVar(0, solver.infinity(), f'Tardiness_{i}') for i in products}

#배송후 제품생산가능
Pro = {i:{j: solver.IntVar(0, 1, f'PrePro_{i}_{j}') for j in materials} for i in products}

#납기지연시간 제약
for i in products:
    solver.Add(Tardiness[i] >= st[i] - due[i])

#원자재 재고 제약
for j in materials:
    solver.Add(sum(PrePro[i][j]*requirements[i][j] for i in products) <= inventory[j])

#배송시시 제약
for j in materials:
    solver.Add(sum(Pro[i][j]*requirements[i][j] for i in products) <= inventory[j] + transit[j]['qty'])

#배송 후 생산가능 제약
for i in products:
    for j in materials:
        solver.Add(Pro[i][j]*M >= transit[j]['lt']-st[i])


#원자재 조달기간 전 생산가능 제약
for i in products:
    for j in materials:
        solver.Add(PrePro[i][j]*M >= lt[j]-st[i])

#납기지연시간 최소화
solver.Minimize(sum(Tardiness[i] for i in products))



# 5. 최적화 실행
status = solver.Solve()

# 결과 출력
if status == pywraplp.Solver.OPTIMAL:
    print("최적화 결과:")
    
    # 각 제품별 생산 시작 시간
    print("\n생산 시작시간:")
    for p in products:
        print(f"{p}: {st[p].solution_value()}")
    
    # 각 제품별 납기 지연 시간
    print("\n납기 지연시간:")
    for p in products:
        print(f"{p}: {Tardiness[p].solution_value()}")
    
    # 각 원자재의 실제 사용량
    print("\n각 원자재의 사용량:")
    for m in materials:
        used_amount = sum(PrePro[p][m].solution_value() * requirements[p].get(m, 0) for p in products)
        print(f"{m}: {used_amount}")
        
    # 총 납기 지연 시간의 합 출력
    total_tardiness = sum(Tardiness[i].solution_value() for i in products)
    # 평균 납기 지연 시간 출력
    average_tardiness = total_tardiness / len(products)

    print(f"\n총 납기 지연 시간: {total_tardiness}")
    print(f"평균 납기 지연 시간: {average_tardiness}")
        
else:
    print("최적해를 찾지 못했습니다.")



import plotly.graph_objects as go
import plotly.express as px

# Gantt 스타일: 생산 시작 시간
fig1 = go.Figure()
fig1.add_trace(go.Bar(
    y=products,
    x=[st[p].solution_value() for p in products],
    orientation='h',
    marker=dict(color='skyblue'),
    name="생산 시작 시간"
))

fig1.update_layout(
    title="제품별 생산 시작 시간",
    xaxis_title="시간",
    yaxis_title="제품",
    template="plotly_white"
)
fig1.write_html("생산_시작시간.html")


# 납기 지연 시간
fig2 = px.bar(
    x=products,
    y=[Tardiness[p].solution_value() for p in products],
    labels={'x': '제품', 'y': '납기 지연 시간'},
    title="제품별 납기 지연 시간",
    color_discrete_sequence=['salmon']
)
fig2.write_html("납기_지연시간.html")


# 원자재 사용량
material_usage = []
for m in materials:
    used_amount = sum(PrePro[p][m].solution_value() * requirements[p].get(m, 0) for p in products)
    material_usage.append(used_amount)

fig3 = px.bar(
    x=materials,
    y=material_usage,
    labels={'x': '원자재', 'y': '사용량'},
    title="원자재별 사용량",
    color_discrete_sequence=['mediumseagreen']
)
fig3.write_html("원자재_사용량.html")
