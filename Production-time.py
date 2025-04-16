from ortools.linear_solver import pywraplp

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
    'R1': 2,
    'R2': 4,
    'R3': 1
}

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

#납기지연시간 제약
for i in products:
    solver.Add(Tardiness[i] >= st[i] - due[i])

#원자재 재고 제약
for j in materials:
    solver.Add(sum(PrePro[i][j]*requirements[i][j] for i in products) <= inventory[j])

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