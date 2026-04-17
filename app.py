from flask import Flask, render_template_string, request, jsonify
import csv
import io

app = Flask(__name__)

def load_taco():
    foods = []
    try:
        with open('data/taco.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    foods.append({
                        'alimento': row['alimento'].strip(),
                        'calorias': float(row['calorias']),
                        'proteina': float(row['proteina']),
                        'carboidrato': float(row['carboidrato']),
                        'gordura': float(row['gordura']),
                        'unidade': row['unidade']
                    })
                except:
                    pass
    except:
        pass
    return foods

def calculate_tmb(weight, height, age, gender):
    if gender == 'M':
        return 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
    else:
        return 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age)

def calculate_calories(tmb, activity_factor):
    return tmb * activity_factor

def calculate_deficit(weight_loss_month):
    return (weight_loss_month * 7700) / 30

def calculate_recommended_calories(get_value, deficit):
    recommended = get_value - deficit
    return max(1200, recommended)

def calculate_macros(calories, protein_pct, carb_pct, fat_pct):
    protein_cal = calories * (protein_pct / 100)
    carb_cal = calories * (carb_pct / 100)
    fat_cal = calories * (fat_pct / 100)
    
    return {
        'proteina': {
            'grams': protein_cal / 4,
            'calories': protein_cal,
            'percent': protein_pct
        },
        'carboidrato': {
            'grams': carb_cal / 4,
            'calories': carb_cal,
            'percent': carb_pct
        },
        'gordura': {
            'grams': fat_cal / 9,
            'calories': fat_cal,
            'percent': fat_pct
        }
    }

def distribute_calories(calories, meal_count, lunch_pct=45, dinner_pct=55):
    main_meals_pct = lunch_pct + dinner_pct
    other_pct = 100 - main_meals_pct
    
    lunch_cal = calories * (lunch_pct / 100)
    dinner_cal = calories * (dinner_pct / 100)
    
    if meal_count > 2:
        other_meals = calories * (other_pct / 100) / (meal_count - 2)
    else:
        other_meals = 0
    
    return {
        'almoco': lunch_cal,
        'janta': dinner_cal,
        'outras': other_meals,
        'total': calories
    }

def get_substitutes(food_name, taco_data):
    substitutes = []
    base_name = food_name.lower().strip()
    
    categories = {
        'arroz': ['Arroz branco cozido', 'Arroz integral cozido', 'Arroz branco cozido', 'Polenta'],
        'feijao': ['Feijão preto cozido', 'Feijão carioca', 'Feijão lentilha', 'Feijão ervilha'],
        'macarrao': ['Macarrão cozido', 'Lasanha massa cozida', 'Nhoque'],
        'batata': ['Batata Inglesa', 'Batata doce', 'Mandioquinha', 'Inhame'],
        'frango': ['Peito de frango', 'Coxa de frango', 'Sobrecoxa', 'Frango desfiado'],
        'carne': ['Carne moída magra', 'Patinho', 'Alcatra', 'Contrafilé'],
        'peixe': ['Tilápia', 'Sardinha assada', 'Atum fresco', 'Pescada'],
        'ovo': ['Ovo inteiro', 'Ovo mexido', 'Ovo cozido', 'Clara'],
        'leite': ['Leite integral', 'Leite desnatado', 'Leite semi desnatado'],
        'queijo': ['Queijo mussarela', 'Queijo ricota', 'Queijo cottage', 'Queijo coalho'],
        'pao': ['Pão francês', 'Pão integral', 'Torrada', 'Biscoito água e sal'],
        'iogurte': ['Iogurte natural', 'Iogurte desnatado', 'Iogurte frutas']
    }
    
    for key, alternatives in categories.items():
        if key in base_name:
            for alt in alternatives:
                if alt.lower() != base_name:
                    for food in taco_data:
                        if food['alimento'].lower() == alt.lower():
                            substitutes.append(food)
                            break
    
    return substitutes[:4] if substitutes else []

def generate_meal_plan(calories, meal_count, taco_data, preferences):
    distribution = distribute_calories(calories, meal_count)
    meals = []
    
    meal_names = ['Café da manhã', 'Almoço', 'Janta']
    if meal_count > 3:
        for i in range(3, meal_count):
            meal_names.insert(i-1, f'Lanche {i-1}')
    elif meal_count == 2:
        meal_names = ['Café da manhã', 'Almoço/janta']
    
    for i in range(meal_count):
        meal = {'name': meal_names[i] if i < len(meal_names) else f'Refeição {i+1}', 'foods': []}
        
        if i == 1:
            target_cal = distribution['almoco']
        elif i == meal_count - 1:
            target_cal = distribution['janta']
        else:
            target_cal = distribution['outras']
        
        if target_cal <= 0:
            target_cal = calories / meal_count
        
        calorie_sum = 0
        selected_foods = []
        
        main_sources = [
            ('arroz branco cozido', 130),
            ('feijao preto cozido', 132),
        ]
        
        for food_name, cal in main_sources:
            for food in taco_data:
                if food['alimento'].lower() == food_name:
                    ratio = min(0.4, target_cal / (cal * 2))
                    qty = ratio * 100
                    selected_foods.append({
                        'alimento': food['alimento'],
                        'quantidade': int(qty),
                        'calorias': round(cal * qty / 100),
                        'proteina': round(food['proteina'] * qty / 100, 1),
                        'carboidrato': round(food['carboidrato'] * qty / 100, 1),
                        'gordura': round(food['gordura'] * qty / 100, 1)
                    })
                    calorie_sum += cal * qty / 100
                    break
        
        proteins = [f for f in taco_data if f['proteina'] > 15]
        for food in proteins[:2]:
            if calorie_sum < target_cal * 0.7:
                remain = target_cal - calorie_sum
                qty = min(150, remain / food['calorias'] * 100)
                selected_foods.append({
                    'alimento': food['alimento'],
                    'quantidade': int(qty),
                    'calorias': round(food['calorias'] * qty / 100),
                    'proteina': round(food['proteina'] * qty / 100, 1),
                    'carboidrato': round(food['carboidrato'] * qty / 100, 1),
                    'gordura': round(food['gordura'] * qty / 100, 1)
                })
                calorie_sum += food['calorias'] * qty / 100
        
        vegetables = [f for f in taco_data if f['carboidrato'] < 10 and f['proteina'] < 3]
        for food in vegetables[:2]:
            if calorie_sum < target_cal * 0.9:
                remain = target_cal - calorie_sum
                qty = min(150, remain / max(food['calorias'], 1) * 100)
                if qty > 0:
                    selected_foods.append({
                        'alimento': food['alimento'],
                        'quantidade': int(qty),
                        'calorias': round(food['calorias'] * qty / 100),
                        'proteina': round(food['proteina'] * qty / 100, 1),
                        'carboidrato': round(food['carboidrato'] * qty / 100, 1),
                        'gordura': round(food['gordura'] * qty / 100, 1)
                    })
                    calorie_sum += food['calorias'] * qty / 100
        
        meal['foods'] = selected_foods
        meal['total_calorias'] = round(calorie_sum)
        meals.append(meal)
    
    return meals

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NutriCalc - Calculadora Nutricional</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #2D6A4F;
            --secondary: #40916C;
            --accent: #95D5B2;
            --light: #D8F3DC;
            --bg: #F8F9FA;
            --card: #FFFFFF;
            --text: #212529;
            --text-light: #6C757D;
            --danger: #DC3545;
            --warning: #FFC107;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Poppins', sans-serif;
            background: var(--bg);
            color: var(--text);
            min-height: 100vh;
        }
        
        .header {
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: white;
            padding: 1.5rem 2rem;
            text-align: center;
            box-shadow: 0 4px 12px rgba(45, 106, 79, 0.3);
        }
        
        .header h1 {
            font-size: 2rem;
            font-weight: 700;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
        }
        
        .header p {
            opacity: 0.9;
            margin-top: 0.5rem;
        }
        
        .container {
            max-width: 900px;
            margin: 2rem auto;
            padding: 0 1rem;
        }
        
        .tabs {
            display: flex;
            gap: 5px;
            background: var(--card);
            border-radius: 12px;
            padding: 5px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            margin-bottom: 1.5rem;
            overflow-x: auto;
        }
        
        .tab {
            padding: 12px 20px;
            border: none;
            background: transparent;
            cursor: pointer;
            border-radius: 8px;
            font-family: inherit;
            font-size: 0.9rem;
            font-weight: 500;
            color: var(--text-light);
            transition: all 0.3s ease;
            white-space: nowrap;
        }
        
        .tab.active {
            background: var(--primary);
            color: white;
        }
        
        .tab:hover:not(.active) {
            background: var(--light);
        }
        
        .card {
            background: var(--card);
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            margin-bottom: 1.5rem;
        }
        
        .card-title {
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--primary);
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .form-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
        }
        
        .form-group {
            margin-bottom: 1rem;
        }
        
        .form-group label {
            display: block;
            font-size: 0.85rem;
            font-weight: 500;
            color: var(--text-light);
            margin-bottom: 0.5rem;
        }
        
        .form-group input, .form-group select, .form-group textarea {
            width: 100%;
            padding: 12px 16px;
            border: 2px solid #E9ECEF;
            border-radius: 8px;
            font-family: inherit;
            font-size: 1rem;
            transition: border-color 0.3s ease;
        }
        
        .form-group input:focus, .form-group select:focus, .form-group textarea:focus {
            outline: none;
            border-color: var(--primary);
        }
        
        .form-group textarea {
            min-height: 80px;
            resize: vertical;
        }
        
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-family: inherit;
            font-size: 1rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .btn-primary {
            background: var(--primary);
            color: white;
        }
        
        .btn-primary:hover {
            background: var(--secondary);
            transform: translateY(-2px);
        }
        
        .btn-secondary {
            background: var(--light);
            color: var(--primary);
        }
        
        .btn-secondary:hover {
            background: var(--accent);
        }
        
        .results-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
        }
        
        .result-card {
            background: var(--light);
            padding: 1.25rem;
            border-radius: 10px;
            text-align: center;
        }
        
        .result-card.highlight {
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: white;
        }
        
        .result-value {
            font-size: 1.75rem;
            font-weight: 700;
            margin: 0.5rem 0;
        }
        
        .result-label {
            font-size: 0.85rem;
            opacity: 0.8;
        }
        
        .table-container {
            overflow-x: auto;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9rem;
        }
        
        th, td {
            padding: 12px 16px;
            text-align: left;
            border-bottom: 1px solid #E9ECEF;
        }
        
        th {
            background: var(--light);
            font-weight: 600;
            color: var(--primary);
        }
        
        tr:hover {
            background: #F8F9FA;
        }
        
        .input-group {
            display: flex;
            gap: 8px;
            align-items: center;
        }
        
        .input-group input {
            width: 80px;
        }
        
        .badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 500;
        }
        
        .badge-success {
            background: #D4EDDA;
            color: #155724;
        }
        
        .badge-warning {
            background: #FFF3CD;
            color: #856404;
        }
        
        .badge-danger {
            background: #F8D7DA;
            color: #721C24;
        }
        
        .meal-card {
            background: var(--light);
            padding: 1.25rem;
            border-radius: 10px;
            margin-bottom: 1rem;
        }
        
        .meal-title {
            font-weight: 600;
            color: var(--primary);
            margin-bottom: 0.75rem;
            display: flex;
            justify-content: space-between;
        }
        
        .meal-calories {
            font-size: 0.85rem;
            color: var(--text-light);
        }
        
        .food-item {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #E9ECEF;
            font-size: 0.9rem;
        }
        
        .food-item:last-child {
            border-bottom: none;
        }
        
        .substitutes {
            margin-top: 0.5rem;
            font-size: 0.8rem;
            color: var(--text-light);
        }
        
        .section-title {
            font-size: 1.1rem;
            font-weight: 600;
            color: var(--text);
            margin: 1.5rem 0 1rem;
        }
        
        .hidden {
            display: none;
        }
        
        .checkbox-group {
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
        }
        
        .checkbox-item {
            display: flex;
            align-items: center;
            gap: 6px;
        }
        
        .checkbox-item input {
            width: auto;
        }
        
        @media (max-width: 600px) {
            .header h1 {
                font-size: 1.5rem;
            }
            
            .form-grid {
                grid-template-columns: 1fr;
            }
            
            .tabs {
                flex-wrap: nowrap;
            }
            
            .tab {
                padding: 10px 14px;
                font-size: 0.8rem;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🥗 NutriCalc</h1>
        <p>Calculadora Nutricional Personalizada</p>
    </div>
    
    <div class="container">
        <div class="tabs">
            <button class="tab active" onclick="showTab('dados')">Dados Pessoais</button>
            <button class="tab" onclick="showTab('resultados')">Resultados</button>
            <button class="tab" onclick="showTab('macros')">Macronutrientes</button>
            <button class="tab" onclick="showTab('refeicoes')">Refeições</button>
            <button class="tab" onclick="showTab('cardapio')">Cardápio</button>
        </div>
        
        <!-- TAB: DADOS PESSOAIS -->
        <div id="tab-dados" class="tab-content">
            <div class="card">
                <h2 class="card-title">📊 Dados Biométricos</h2>
                <div class="form-grid">
                    <div class="form-group">
                        <label>Peso (kg)</label>
                        <input type="number" id="weight" step="0.1" min="30" max="200" placeholder="Ex: 70" required>
                    </div>
                    <div class="form-group">
                        <label>Altura (cm)</label>
                        <input type="number" id="height" min="100" max="220" placeholder="Ex: 170" required>
                    </div>
                    <div class="form-group">
                        <label>Idade (anos)</label>
                        <input type="number" id="age" min="10" max="100" placeholder="Ex: 30" required>
                    </div>
                    <div class="form-group">
                        <label>Sexo</label>
                        <select id="gender">
                            <option value="M">Masculino</option>
                            <option value="F">Feminino</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Fator de Atividade</label>
                        <select id="activity">
                            <option value="1.2">Sedentário (pouco movimento)</option>
                            <option value="1.375">Levemente ativo (1-3 dias/semana)</option>
                            <option value="1.55">Moderadamente ativo (3-5 dias/semana)</option>
                            <option value="1.725">Muito ativo (6-7 dias/semana)</option>
                            <option value="1.9">Atleta (treino intenso)</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Meta de perda de peso (kg/mês)</label>
                        <input type="number" id="weight_loss" step="0.1" min="0" max="5" placeholder="Ex: 2" value="2">
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h2 class="card-title">🍽️ Preferências Alimentares</h2>
                <div class="form-grid">
                    <div class="form-group">
                        <label>Quantas refeições por dia?</label>
                        <select id="meal_count">
                            <option value="2">2 refeições</option>
                            <option value="3" selected>3 refeições</option>
                            <option value="4">4 refeições</option>
                            <option value="5">5 refeições</option>
                            <option value="6">6 refeições</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Possui restrições religiosas/éticas?</label>
                        <select id="restrictions">
                            <option value="">Nenhuma</option>
                            <option value="vegetariano">Vegetariano</option>
                            <option value="vegano">Vegano</option>
                            <option value="kosher">Kosher</option>
                            <option value="halal">Halal</option>
                        </select>
                    </div>
                </div>
                <div class="form-group">
                    <label>Doenças ou condições especiais</label>
                    <select id="disease">
                        <option value="">Nenhuma</option>
                        <option value="diabetes">Diabetes</option>
                        <option value="hipertensao">Hipertensão</option>
                        <option value="colesterol">Colesterol alto</option>
                        <option value="gota">Gota</option>
                        <option value="renal">Doença renal</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Alimentos que NÃO pode comer</label>
                    <textarea id="dislikes" placeholder="Liste alimentos que você não pode ou não gosta de comer (ex: feijão, ovo, leite)"></textarea>
                </div>
                <div class="form-group">
                    <label>Alimentos Obrigatórios (que devem estar presentes)</label>
                    <textarea id="required_foods" placeholder="Liste alimentos que você sempre quer nas refeições (ex: arroz, frango)"></textarea>
                </div>
            </div>
            
            <div class="card">
                <h2 class="card-title">⚙️ Distribuição de Calorias</h2>
                <p style="font-size: 0.9rem; color: var(--text-light); margin-bottom: 1rem;">
                    Por padrão, 50% das calorias ficam para almoço e janta (45% + 55%). Os outros 50% são distribuídos entre as demais refeições.
                </p>
                <div class="form-grid">
                    <div class="form-group">
                        <label>% Almoço (de 50%)</label>
                        <input type="number" id="lunch_pct" value="45" min="0" max="100">
                    </div>
                    <div class="form-group">
                        <label>% Janta (de 50%)</label>
                        <input type="number" id="dinner_pct" value="55" min="0" max="100">
                    </div>
                </div>
            </div>
            
            <button class="btn btn-primary" onclick="calculate()">Calcular</button>
        </div>
        
        <!-- TAB: RESULTADOS -->
        <div id="tab-resultados" class="tab-content hidden">
            <div class="card">
                <h2 class="card-title">📈 Resultados dos Cálculos</h2>
                <div class="results-grid">
                    <div class="result-card">
                        <div class="result-label">Taxa de Metabolismo Basal</div>
                        <div class="result-value" id="tmb-result">--</div>
                        <div class="result-label">kcal/dia</div>
                    </div>
                    <div class="result-card">
                        <div class="result-label">Gasto Energético Total</div>
                        <div class="result-value" id="get-result">--</div>
                        <div class="result-label">kcal/dia</div>
                    </div>
                    <div class="result-card">
                        <div class="result-label">Déficit Diário</div>
                        <div class="result-value" id="deficit-result">--</div>
                        <div class="result-label">kcal/dia</div>
                    </div>
                    <div class="result-card highlight">
                        <div class="result-label">Calorias Diárias Recomendadas</div>
                        <div class="result-value" id="recommended-result">--</div>
                        <div class="result-label">kcal/dia para atingir sua meta</div>
                    </div>
                </div>
                <p style="margin-top: 1rem; font-size: 0.85rem; color: var(--text-light);">
                    * Cálculo baseado na fórmula de Mifflin-St Jeor. A meta de perda considera ~7700 kcal por kg de gordura.
                </p>
            </div>
        </div>
        
        <!-- TAB: MACRONUTRIENTES -->
        <div id="tab-macros" class="tab-content hidden">
            <div class="card">
                <h2 class="card-title">🥩 Distribuição de Macronutrientes</h2>
                <p style="font-size: 0.9rem; color: var(--text-light); margin-bottom: 1rem;">
                    Altere os percentuais conforme sua preferência. O total deve somar 100%.
                </p>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Macronutriente</th>
                                <th>Percentual (%)</th>
                                <th>Gramas</th>
                                <th>Calorias</th>
                            </tr>
                        </thead>
                        <tbody id="macros-table">
                            <tr>
                                <td><strong>🥩 Proteína</strong></td>
                                <td>
                                    <div class="input-group">
                                        <input type="number" id="protein-pct" value="30" min="0" max="100" onchange="recalculateMacros()">
                                        <span>%</span>
                                    </div>
                                </td>
                                <td id="protein-grams">--</td>
                                <td id="protein-cal">--</td>
                            </tr>
                            <tr>
                                <td><strong>🍚 Carboidrato</strong></td>
                                <td>
                                    <div class="input-group">
                                        <input type="number" id="carb-pct" value="40" min="0" max="100" onchange="recalculateMacros()">
                                        <span>%</span>
                                    </div>
                                </td>
                                <td id="carb-grams">--</td>
                                <td id="carb-cal">--</td>
                            </tr>
                            <tr>
                                <td><strong>🥑 Gordura</strong></td>
                                <td>
                                    <div class="input-group">
                                        <input type="number" id="fat-pct" value="30" min="0" max="100" onchange="recalculateMacros()">
                                        <span>%</span>
                                    </div>
                                </td>
                                <td id="fat-grams">--</td>
                                <td id="fat-cal">--</td>
                            </tr>
                            <tr style="background: var(--light);">
                                <td><strong>Total</strong></td>
                                <td id="total-pct"><strong>100%</strong></td>
                                <td>--</td>
                                <td id="total-cal">--</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                <p id="macro-warning" style="margin-top: 1rem; font-size: 0.85rem; color: var(--danger); display: none;">
                    ⚠️ Os percentuais devem somar 100%!
                </p>
            </div>
        </div>
        
        <!-- TAB: REFEIÇÕES -->
        <div id="tab-refeicoes" class="tab-content hidden">
            <div class="card">
                <h2 class="card-title">🍽️ Distribuição de Calorias por Refeição</h2>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Refeição</th>
                                <th>Percentual</th>
                                <th>Calorias</th>
                            </tr>
                        </thead>
                        <tbody id="meals-distribution">
                            <tr>
                                <td>Almoço</td>
                                <td id="lunch-dist-pct">45%</td>
                                <td id="lunch-dist-cal">--</td>
                            </tr>
                            <tr>
                                <td>Janta</td>
                                <td id="dinner-dist-pct">55%</td>
                                <td id="dinner-dist-cal">--</td>
                            </tr>
                            <tr>
                                <td>Outras refeições</td>
                                <td>50%</td>
                                <td id="others-dist-cal">--</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        
        <!-- TAB: CARDÁPIO -->
        <div id="tab-cardapio" class="tab-content hidden">
            <div class="card">
                <h2 class="card-title">📋 Cardápio Sugerido</h2>
                <p style="font-size: 0.9rem; color: var(--text-light); margin-bottom: 1rem;">
                    Cardápio calculado com base na TACO (Tabela Brasileira de Composição de Alimentos).
                </p>
                <div id="meal-plans">
                    <!-- Meal plans will be inserted here -->
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let tacoData = [];
        let calculatedData = null;
        
        // Load TACO data
        async function loadTaco() {
            try {
                const response = await fetch('/get-taco');
                if (response.ok) {
                    tacoData = await response.json();
                }
            } catch(e) {
                console.log('Using fallback taco data');
            }
        }
        
        function showTab(tabName) {
            document.querySelectorAll('.tab-content').forEach(tab => tab.classList.add('hidden'));
            document.getElementById('tab-' + tabName).classList.remove('hidden');
            
            document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
            event.target.classList.add('active');
        }
        
        function calculate() {
            const weight = parseFloat(document.getElementById('weight').value);
            const height = parseFloat(document.getElementById('height').value);
            const age = parseInt(document.getElementById('age').value);
            const gender = document.getElementById('gender').value;
            const activity = parseFloat(document.getElementById('activity').value);
            const weight_loss = parseFloat(document.getElementById('weight_loss').value) || 0;
            
            if (!weight || !height || !age) {
                alert('Por favor, preencha todos os dados biométricos!');
                return;
            }
            
            // Calculate TMB
            let tmb;
            if (gender === 'M') {
                tmb = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age);
            } else {
                tmb = 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age);
            }
            
            // Calculate GET
            const get = tmb * activity;
            
            // Calculate deficit
            const deficit = (weight_loss * 7700) / 30;
            
            // Calculate recommended calories
            const recommended = Math.max(1200, get - deficit);
            
            // Store data
            calculatedData = { tmb, get, deficit, recommended, weight, weight_loss };
            
            // Show results
            document.getElementById('tmb-result').textContent = Math.round(tmb);
            document.getElementById('get-result').textContent = Math.round(get);
            document.getElementById('deficit-result').textContent = Math.round(deficit);
            document.getElementById('recommended-result').textContent = Math.round(recommended);
            
            // Update macros
            recalculateMacros();
            
            // Update meal distribution
            updateMealDistribution();
            
            // Generate meal plan
            generateMealPlan();
            
            // Switch to results tab
            showTab('resultados');
            document.querySelectorAll('.tab')[1].classList.add('active');
            document.querySelectorAll('.tab')[0].classList.remove('active');
        }
        
        function recalculateMacros() {
            if (!calculatedData) return;
            
            const proteinPct = parseFloat(document.getElementById('protein-pct').value) || 30;
            const carbPct = parseFloat(document.getElementById('carb-pct').value) || 40;
            const fatPct = parseFloat(document.getElementById('fat-pct').value) || 30;
            
            const total = proteinPct + carbPct + fatPct;
            document.getElementById('total-pct').innerHTML = '<strong>' + total + '%</strong>';
            document.getElementById('macro-warning').style.display = total !== 100 ? 'block' : 'none';
            
            const calories = calculatedData.recommended;
            
            const proteinCal = calories * (proteinPct / 100);
            const carbCal = calories * (carbPct / 100);
            const fatCal = calories * (fatPct / 100);
            
            const proteinGrams = proteinCal / 4;
            const carbGrams = carbCal / 4;
            const fatGrams = fatCal / 9;
            
            document.getElementById('protein-grams').textContent = Math.round(proteinGrams) + 'g';
            document.getElementById('protein-cal').textContent = Math.round(proteinCal) + 'kcal';
            document.getElementById('carb-grams').textContent = Math.round(carbGrams) + 'g';
            document.getElementById('carb-cal').textContent = Math.round(carbCal) + 'kcal';
            document.getElementById('fat-grams').textContent = Math.round(fatGrams) + 'g';
            document.getElementById('fat-cal').textContent = Math.round(fatCal) + 'kcal';
            document.getElementById('total-cal').textContent = Math.round(proteinCal + carbCal + fatCal) + 'kcal';
        }
        
        function updateMealDistribution() {
            if (!calculatedData) return;
            
            const lunchPct = parseFloat(document.getElementById('lunch_pct').value) || 45;
            const dinnerPct = parseFloat(document.getElementById('dinner_pct').value) || 55;
            const mealCount = parseInt(document.getElementById('meal_count').value);
            
            const calories = calculatedData.recommended;
            const mainMealsPct = lunchPct + dinnerPct;
            const otherPct = 100 - mainMealsPct;
            
            const lunchCal = calories * (lunchPct / 100);
            const dinnerCal = calories * (dinnerPct / 100);
            const othersCal = mealCount > 2 ? calories * (otherPct / 100) / (mealCount - 2) : 0;
            
            document.getElementById('lunch-dist-pct').textContent = lunchPct + '%';
            document.getElementById('lunch-dist-cal').textContent = Math.round(lunchCal) + ' kcal';
            document.getElementById('dinner-dist-pct').textContent = dinnerPct + '%';
            document.getElementById('dinner-dist-cal').textContent = Math.round(dinnerCal) + ' kcal';
            document.getElementById('others-dist-cal').textContent = mealCount > 2 ? Math.round(othersCal) + ' kcal/refeição' : '--';
        }
        
        function generateMealPlan() {
            if (!calculatedData) return;
            
            const mealCount = parseInt(document.getElementById('meal_count').value);
            const calories = calculatedData.recommended;
            const lunchPct = parseFloat(document.getElementById('lunch_pct').value) || 45;
            const dinnerPct = parseFloat(document.getElementById('dinner_pct').value) || 55;
            
            const mainMealsPct = lunchPct + dinnerPct;
            const otherPct = 100 - mainMealsPct;
            
            const lunchCal = calories * (lunchPct / 100);
            const dinnerCal = calories * (dinnerPct / 100);
            const otherCal = mealCount > 2 ? calories * (otherPct / 100) / (mealCount - 2) : 0;
            
            const mealNames = ['Café da manhã', 'Almoço', 'Janta'];
            if (mealCount > 3) {
                for (let i = 3; i < mealCount; i++) {
                    mealNames.splice(i - 1, 0, 'Lanche ' + (i - 1));
                }
            }
            
            const meals = [];
            for (let i = 0; i < mealCount; i++) {
                let targetCal;
                if (i === 1) {
                    targetCal = lunchCal;
                } else if (i === mealCount - 1) {
                    targetCal = dinnerCal;
                } else {
                    targetCal = otherCal;
                }
                
                meals.push({
                    name: mealNames[i] || 'Refeição ' + (i + 1),
                    calories: Math.round(targetCal)
                });
            }
            
            const mealPlans = document.getElementById('meal-plans');
            mealPlans.innerHTML = meals.map((meal, idx) => `
                <div class="meal-card">
                    <div class="meal-title">
                        <span>${meal.name}</span>
                        <span class="meal-calories">${meal.calories} kcal</span>
                    </div>
                    <div class="food-item">
                        <span>Arroz branco (100g)</span>
                        <span>~130 kcal</span>
                    </div>
                    <div class="food-item">
                        <span>Feijão preto (100g)</span>
                        <span>~132 kcal</span>
                    </div>
                    <div class="food-item">
                        <span>Peito de frango (100g)</span>
                        <span>~165 kcal</span>
                    </div>
                    <div class="food-item">
                        <span>Legumes variados (150g)</span>
                        <span>~50 kcal</span>
                    </div>
                    <div class="substitutes">
                        <strong>Substitutos:</strong> Arroz integral, Feijão carioca, Coxa de frango, Batata doce
                    </div>
                </div>
            `).join('');
        }
        
        // Initialize
        loadTaco();
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/get-taco')
def get_taco():
    foods = load_taco()
    return jsonify(foods)

if __name__ == '__main__':
    app.run(debug=True, port=5000)