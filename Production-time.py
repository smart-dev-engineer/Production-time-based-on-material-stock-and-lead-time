from docplex.mp.model import Model
import random

# 설정
transit_option = False
M = 100000

# 제품 및 원자재 수 설정
num_products = 10
num_materials = 15

# 제품 및 원자재 리스트 생성
products = [f'P{i+1}' for i in range(num_products)]
materials = [f'R{i+1}' for i in range(num_materials)]

# 제품별 납기일 (5~20일 사이 랜덤)
due = {product: random.randint(5, 20) for product in products}

# 원자재 조달기간 (15~30일 사이 랜덤)
lt = {material: random.randint(15, 30) for material in materials}

# 원자재 재고 (50~200 사이 랜덤)
inventory = {material: random.randint(20, 60) for material in materials}

# 제품별 원자재 소요량 (10~20개 중 랜덤 선택, 수요 3~10)
requirements = {}
for product in products:
    requirements[product] = {}
    used_materials = random.sample(materials, k=random.randint(10, num_materials))
    for material in materials:
        requirements[product][material] = random.randint(3, 10) if material in used_materials else 0

# 빠른 조달 옵션
if transit_option:
    transit = {
        material: {'lt': random.randint(0, 5), 'qty': random.randint(20, 100)}
        for material in materials
    }
else:
    transit = {
        material: {'lt': 0, 'qty': 0}
        for material in materials
    }

# CPLEX 모델 생성
mdl = Model(name="Production_Scheduling")

# 변수 정의
st = {p: mdl.continuous_var(lb=0, name=f"st_{p}") for p in products}
tardiness = {p: mdl.continuous_var(lb=0, name=f"Tardiness_{p}") for p in products}
PrePro = {p: {m: mdl.binary_var(name=f"PrePro_{p}_{m}") for m in materials} for p in products}
Pro = {p: {m: mdl.binary_var(name=f"Pro_{p}_{m}") for m in materials} for p in products}

# 제약조건

# 납기 지연 제약
for p in products:
    mdl.add_constraint(tardiness[p] >= st[p] - due[p], ctname=f"Tardiness_Constraint_{p}")

# 원자재 재고 제약
for m in materials:
    mdl.add_constraint(
        mdl.sum(PrePro[p][m] * requirements[p][m] for p in products) <= inventory[m],
        ctname=f"Inventory_Constraint_{m}"
    )

# 원자재 조달기간 내 생산 가능 제약
for p in products:
    for m in materials:
        mdl.add_constraint(
            PrePro[p][m] * M >= lt[m] - st[p],
            ctname=f"StandardLT_{p}_{m}"
        )

# 빠른 조달 사용 시 제약
if transit_option:
    for m in materials:
        mdl.add_constraint(
            mdl.sum(Pro[p][m] * requirements[p][m] for p in products) <= inventory[m] + transit[m]['qty'],
            ctname=f"Transit_Inventory_{m}"
        )

    for p in products:
        for m in materials:
            mdl.add_constraint(
                Pro[p][m] * M >= transit[m]['lt'] - st[p],
                ctname=f"TransitLT_{p}_{m}"
            )

# 목적함수: 납기 지연 최소화
mdl.minimize(mdl.sum(tardiness[p] for p in products))

# 최적화 수행
solution = mdl.solve(log_output=True)

# 결과 출력
if solution:
    print("최적화 결과:\n")

    print("생산 시작시간:")
    for p in products:
        print(f"{p}: {st[p].solution_value:.2f}")

    print("\n납기 지연시간:")
    for p in products:
        print(f"{p}: {tardiness[p].solution_value:.2f}")

    # print("\n각 원자재의 사용량:")
    # for m in materials:
    #     used_amount = sum(PrePro[p][m].solution_value * requirements[p][m] for p in products)
    #     print(f"{m}: {used_amount:.2f}")

    total_tardiness = sum(tardiness[p].solution_value for p in products)
    average_tardiness = total_tardiness / len(products)
    print(f"\n총 납기 지연 시간: {total_tardiness:.2f}")
    print(f"평균 납기 지연 시간: {average_tardiness:.2f}")
else:
    print("최적해를 찾지 못했습니다.")
