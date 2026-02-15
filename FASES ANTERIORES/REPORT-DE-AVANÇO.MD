# Relatório de Avanço - CardioIA

Este relatório detalha o status e as entregas de cada fase do projeto CardioIA, baseado na análise do repositório clonado `CARDIO-IA-FASE4`.

## Visão Geral
O projeto CardioIA é uma iniciativa acadêmica progressiva (FIAP) que visa criar um ecossistema completo de cardiologia inteligente. O projeto evolui a cada fase, integrando novas tecnologias como IoT, Machine Learning e Visão Computacional.

---

## 🛑 Fase 1 - CardioIA (Legado)
**Status:** ⚠️ Não disponível no repositório atual.

**Observações:**
- A pasta `FASES/Fase1` contém apenas um aviso indicando que o repositório original (`https://github.com/FernandoSegregio/CardioIA`) está inacessível (Erro 404).
- **Ação Recomendada:** Entrar em contato com o integrante Fernando Segregio para tentar recuperar os arquivos locais da Fase 1, se necessário para histórico.

---

## 🧠 Fase 2 - Diagnóstico Automatizado (IA & NLP)
**Status:** ✅ Completa e documentada em `FASES/Fase2`.

**Foco:** Implementação de inteligência artificial para triagem e diagnóstico inicial.

**Principais Entregas Identificadas:**
1.  **NLP para Sintomas (`src/diagnose.py`):**
    - Engine de processamento de linguagem natural que extrai sintomas de textos relatados por pacientes.
    - Mapeia sintomas para possíveis doenças cardiovasculares usando uma base de conhecimento (`data/knowledge_map.csv`).
2.  **Classificador de Risco (`notebooks/risk_classifier.ipynb`):**
    - Modelo de Machine Learning (Regressão Logística) treinado com TF-IDF.
    - Classifica o risco cardiovascular com base em descrições clínicas.
3.  **Portal Web (`portal/`):**
    - Aplicação Frontend moderna construída com **React 18** e **Vite**.
    - Inclui autenticação, dashboard, gestão de pacientes e agendamentos.
4.  **Análise de ECG (Deep Learning):**
    - Modelo MLP (Multi-Layer Perceptron) usando Keras/TensorFlow para classificação de imagens de eletrocardiogramas (mencionado como "Ir Além").

---

## 📡 Fase 3 - Monitoramento Contínuo (IoT & Series Temporais)
**Status:** ✅ Completa e documentada em `FASE3/`.

**Foco:** Monitoramento de sinais vitais em tempo real usando Internet das Coisas (IoT).

**Principais Entregas Identificadas:**
1.  **Dispositivo IoT (ESP32):**
    - Simulação no Wokwi integrando sensor DHT22 e botão de pulso (BPM).
    - Utiliza sistema de arquivos SPIFFS para resiliência (armazenamento offline caso a rede caia).
2.  **Infraestrutura de Mensageria:**
    - Comunicação via **MQTT** seguro (TLS 8883) usando HiveMQ Cloud.
3.  **Dashboard e Fluxos:**
    - **Node-RED:** Fluxos para processamento de dados e dashboard visual para monitoramento em tempo real.
4.  **Backend e Alertas:**
    - API REST (FastAPI) para regras de negócio e disparo de alertas por e-mail quando sinais vitais excedem limites seguros.
5.  **Análise de Dados:**
    - Notebook Jupyter para detecção de anomalias em séries temporais de BPM e temperatura.

---

## 👁️ Fase 4 - Visão Computacional na Clínica (Atual)
**Status:** 🚧 Fase Atual / Entregue em `FASE4/`.

**Foco:** Aplicação de Visão Computacional para suporte ao diagnóstico por imagem.

**Principais Entregas Identificadas:**
1.  **Pipeline de Visão Computacional (`notebooks/phase4_cv.ipynb`):**
    - Pré-processamento de imagens médicas (Raio-X).
    - Implementação de redes neurais convolucionais (CNNs).
    - Uso de **Transfer Learning** (com arquiteturas como VGG ou ResNet) para melhorar a precisão do diagnóstico.
2.  **Protótipo de Aplicação (`app/`):**
    - Aplicação Web simples (Flask) que serve o modelo treinado (`model.pt`).
    - Permite o upload de imagens para classificação automática.
3.  **Relatórios e Métricas:**
    - Análise de performance do modelo (Acurácia, Precisão, Recall, F1-Score).
    - Discussão sobre ética e fairness em IA médica.

---

## Conclusão
O repositório está bem estruturado, separando claramente as fases 2, 3 e 4. A perda dos dados da Fase 1 é o único ponto de atenção quanto à integridade histórica. O projeto demonstra uma evolução técnica consistente, partindo de algoritmos clássicos (Fase 2) para IoT (Fase 3) e Deep Learning visual (Fase 4).
