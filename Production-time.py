from ortools.linear_solver import pywraplp
import matplotlib.pyplot as plt
# 1. OR-Tools solver 생성
solver = pywraplp.Solver.CreateSolver('SCIP')

#Big-M
M = 10000

################입력변수#######################

#라인수
ln = 2
lines = ['line1', 'line2']

# 제품
products = ['P1', 'P2', 'P3', 'P4', 'P5']
start_p = ['start']
end_p = ['end']

#납기일
due = {
    'P1': 5,
    'P2': 5,
    'P3': 5,
    'P4': 5,
    'P5': 5
}
# 제품별 생산시간 (단위: 시간)
process_time = {
    'P1': 4,
    'P2': 2,
    'P3': 3,
    'P4': 5,
    'P5': 3
}


# 원자재 수
materials = ['R1', 'R2', 'R3']


# 원자재 조달기간1
lt1 = {
    'R1': {'lt': 2, 'qty': 30},
    'R2': {'lt': 3, 'qty': 30},
    'R3': {'lt': 0, 'qty': 30},
}

# 원자재 조달기간2
lt2= {
    'R1': 5,
    'R2': 10,
    'R3': 1
}



# 각 제품별 원자재 리스트에 없는 원자재는 0으로 설정
for material in materials:
    if material not in lt1:
        lt1[material]['lt'] = 0
        lt1[material]['qty'] = 0



# 원자재 재고
inventory = {
    'R1': 100,
    'R2': 100,
    'R3': 100,
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
for p in requirements:
    for material in materials:
        if material not in requirements[p]:
            requirements[p][material] = 0



# due, process_time, requirements에 더미 작업 추가
due['start'] = 0
due['end'] = 0

process_time['start'] = 0
process_time['end'] = 0

requirements['start'] = {'R1': 0, 'R2': 0, 'R3': 0}
requirements['end'] = {'R1': 0, 'R2': 0, 'R3': 0}

#####################################종속변수#########################################################

#제품별 작업순서
x = {i:{j : solver.IntVar(0, 1, f'x_{i}_{j}') for j in products+start_p+end_p} for i in products+start_p+end_p}

#라인별 작업 할당
y = {l:{i : solver.IntVar(0, 1, f'y_{l}_{i}') for i in products+end_p} for l in lines}

#각 라인별 시작작업
w = {l:{i : solver.IntVar(0, 1, f'w_{l}_{i}') for i in products+end_p} for l in lines}

#제품별 생산시작시간
st = {i: solver.IntVar(0, solver.infinity(), f'st_{i}') for i in products+start_p+end_p}

#제품별 작업종료시간
et = {i: solver.IntVar(0, solver.infinity(), f'st_{i}') for i in products+start_p+end_p}

#배송후 제품생산가능
PrePro1 = {i:{m: solver.IntVar(0, 1, f'PrePro_{i}_{m}') for m in materials} for i in products}

#각 제품별 원자재 조달 전 생산 가능여부
PrePro2 = {i:{m: solver.IntVar(0, 1, f'PrePro_{i}_{m}') for m in materials} for i in products}

#제품별 납기지연시간
Tardiness = {i: solver.IntVar(0, solver.infinity(), f'Tardiness_{i}') for i in products}





#####################################제약식##############################################################

#시작작업수는 라인수보다 많을 수 없다.
for i in start_p:
    solver.Add(sum(x[i][j] for j in products+end_p) <= ln)

#선행작업i의 후행작업은 1개만 올 수 있다.
for i in products:
    solver.Add(sum(x[i][j] for j in products+start_p+end_p) == 1)

#후행작업j의 선행작업은 1개만 올 수 있다.
for j in products:
    solver.Add(sum(x[i][j] for i in products+start_p) == 1)

#각 작업은 선행과 후행 존재
for j in products:
    solver.Add(sum(x[i][j] for i in products+start_p) - sum(x[j][k] for k in products+end_p) == 0)

#시작작업 제약
for l in lines:
    for i in products+end_p:
        solver.Add(w[l][i] <= x['start'][i])
        solver.Add(w[l][i] <= y[l][i])
        solver.Add(w[l][i] >= x['start'][i] + y[l][i] - 1)


#각 라인에 시작작업은 1개만 할당가능
for l in lines:
    solver.Add(sum(w[l][i] for i in products+end_p) == 1)

#작업은 라인에서 1개만 할당가능
for i in products:
    solver.Add(sum(y[l][i] for l in lines) == 1)

for i in products:
    for j in products:
        for l in lines:
            solver.Add(y[l][j] >= x[i][j]+y[l][i] -1)



#작업i다음에는 작업i가 올 수 없음
for i in products+start_p+end_p:
    solver.Add(x[i][i] == 0)

#작업 j는 작업i가 끝난후에 시작할 수 있음
for i in products+start_p:
    for j in products+end_p:
        solver.Add(st[j] >= st[i] + process_time[i]- M * (1 - x[i][j]))

#각 작업의 종료시간은 작업시작시간+작업시간
for i in products:
    solver.Add(et[i] == st[i]+process_time[i])

#납기지연시간 제약
for i in products:
    solver.Add(Tardiness[i] >= et[i] - due[i])

#원자재 재고 제약
for m in materials:
    solver.Add(sum(PrePro2[i][m]*requirements[i][m] for i in products) <= inventory[m])

#배송시 제약
for m in materials:
    solver.Add(sum(PrePro1[i][m]*requirements[i][m] for i in products) <= inventory[m] + lt1[m]['qty'])

#배송 후 생산가능 제약
for i in products:
    for m in materials:
        solver.Add(PrePro1[i][m]*M >= lt1[m]['lt']-st[i])


#원자재 조달기간 전 생산가능 제약
for i in products:
    for m in materials:
        solver.Add(PrePro2[i][m]*M >= lt2[m]-st[i])




#######################최적화시작########################################
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
    
        
    # 총 납기 지연 시간의 합 출력
    total_tardiness = sum(Tardiness[i].solution_value() for i in products)
    # 평균 납기 지연 시간 출력
    average_tardiness = total_tardiness / len(products)

    print(f"\n총 납기 지연 시간: {total_tardiness}")
    print(f"평균 납기 지연 시간: {average_tardiness}")

    print("\n작업 순서 (x[i][j] == 1 인 경우):")
    for i in products + start_p + end_p:
        for j in products + start_p + end_p:
            if x[i][j].solution_value() == 1:
                print(f"{i} → {j}")

    print("\n라인 할당 (y[l][i] == 1 인 경우):")
    for l in lines:
        for i in products:
            if y[l][i].solution_value() == 1:
                print(f"{i} → {l}")
    
    print("\n라인별 시작 작업 (w[l][i] == 1 인 경우):")
    for l in lines:
        for i in products + end_p:
            if w[l][i].solution_value() == 1:
                print(f"{l}의 시작 작업: {i}")

        
else:
    print("최적해를 찾지 못했습니다.")



import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(10, 5))

colors = ['skyblue', 'salmon', 'limegreen', 'gold', 'orchid']
y_ticks = []
y_labels = []

for idx, p in enumerate(products):
    start = st[p].solution_value()
    duration = process_time[p]
    ax.barh(y=idx, width=duration, left=start, height=0.4, color=colors[idx % len(colors)])
    ax.text(start + duration / 2, idx, p, va='center', ha='center', color='black', fontsize=10)
    y_ticks.append(idx)
    y_labels.append(p)

ax.set_yticks(y_ticks)
ax.set_yticklabels(y_labels)
ax.set_xlabel("time")
ax.grid(True)

plt.tight_layout()
plt.show()