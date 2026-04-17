# NutriCalc - Aplicativo de Cálculo Nutricional

## 1. Project Overview

**Nome do Projeto:** NutriCalc
**Tipo:** Aplicativo Web (Flask + HTML/CSS/JS)
**Funcionalidade Principal:** Calcula necessidades calóricas e gera plano alimentar personalizado com base em dados biométricos, meta de emagrecimento e restrições alimentares do usuário.
**Usuários Alvo:** Pessoas que desejam emagrecer de forma saudável e controlada.

## 2. UI/UX Specification

### Layout Structure

- **Header:** Logo "NutriCalc" com ícone de nutritionist
- **Navegação por abas:**
  1. Dados Pessoais
  2. Resultados
  3. Macros
  4. Distribuição de Refeições
  5. Cardápio
- **Container central:** 900px max-width, centralizado

### Visual Design

**Cores:**
- Primary: `#2D6A4F` (verde escuro)
- Secondary: `#40916C` (verde médio)
- Accent: `#95D5B2` (verde claro)
- Background: `#F8F9FA`
- Card: `#FFFFFF`
- Text Primary: `#212529`
- Text Secondary: `#6C757D`
- Danger: `#DC3545`
- Warning: `#FFC107`

**Tipografia:**
- Font Family: 'Poppins', sans-serif
- Heading 1: 28px, weight 700
- Heading 2: 22px, weight 600
- Body: 16px, weight 400
- Small: 14px

**Espaçamento:**
- Section padding: 24px
- Element gap: 16px
- Border radius: 12px

**Efeitos:**
- Sombras suaves nos cards: `0 4px 12px rgba(0,0,0,0.08)`
- Transições: 0.3s ease
- Hover nos botões: escala 1.02

### Componentes

- Formulários com labels flutuantes
- Cards com bordas suaves
- Abas interativas
- Tabelas com zebra striping
- Inputs com foco em verde
- Botões primário/secondary/outline

## 3. Functionality Specification

### Fluxo Principal

1. **Dados Pessoais:**
   - Peso (kg)
   - Altura (cm)
   - Idade (anos)
   - Sexo (M/F)
   - Fator de atividade (1.2 a 1.9)
   - Meta de perda de peso (kg/mês)

2. **Cálculos:**
   - **TMB (Taxa de Metababolismo Basal):**
     - Homens: 88.362 + (13.397 × peso) + (4.799 × altura) - (5.677 × idade)
     - Mulheres: 447.593 + (9.247 × peso) + (3.098 × altura) - (4.330 × idade)
   - **GET (Gasto Energético Total):** TMB × fator_atividade
   - **Deficit diário:** (meta_peso × 7700) / 30 (7700 kcal por kg de gordura)
   - **Calorias diarias recomendada:** GET - deficit

3. **Macronutrientes:**
   - Padrão: Proteína 30%, Carboidrato 40%, Gordura 30%
   - Calorias por grama: proteína 4kcal, carboidrato 4kcal, gord9kcal
   - Campos editáveis para alterar percentuais (com recálculo automático)

4. **Restrições Alimentares:**
   - Refeições por dia (2-6)
   - Alimentos obrigatórios
   - Restrições religiosas/éticas
   - Doenças (diabetes, hipertensão, etc.)
   - Alimentos dislikes

5. **Distribuição de Calorias:**
   - Padrão: 45% almoço, 55% janta = 50% das 2 principais
   - 50% restante dividido entre outras refeições
   - Percentuais personalizáveis

6. **Cardápio (TACO):**
   - Utilizar tabela TACO para Suggestions
   - Substitutos automáticos para variedade
   - Alocar 50% das calorias para almoço+janta

### Validações

- Peso: 30-200 kg
- Altura: 100-220 cm
- Idade: 10-100 anos
- Meta perda: 0.5-5 kg/mês (saudável)
- Percentuais macros: 0-100% (devem somar 100%)

## 4. Acceptance Criteria

- [ ] Usuário consegue inserir todos os dados pessoais
- [ ] Cálculos de TMB, GET e calorias diárias estão corretos
- [ ] Macros são exibidos com грамас e percentuais
- [ ] Usuário pode alterar percentuais e valores recalculam
- [ ] Cardápio é gerando com base na TACO
- [ ] Restrições são respeitadas no cardápio
- [ ] Distribuição de calorias funciona corretamente
- [ ] Interface é responsiva e amigável