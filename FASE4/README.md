# CardioIA - Fase 4: Visao Computacional na Clinica

Prototipo de assistente cardiologico com foco em visao computacional: pre-processamento de imagens medicas simuladas, CNN baseline + transfer learning e entrega dos resultados em notebook ou app simples.

## Ambiente (usado aqui)
- Python 3.13
- PyTorch nightly CPU (2.10.0.dev20251205), torchvision 0.25.0.dev20251205, torchaudio 2.10.0.dev20251205
- Pacotes: scikit-learn, pandas, matplotlib, seaborn, opencv-python, scikit-image, notebook, tqdm, flask
- Venv: `.venv` (ativar com `.\\.venv\\Scripts\\activate`)

## Entregaveis (fase)
- Notebook de pre-processamento (train/val/test, normalizacao, resize).
- Notebook de classificacao: CNN do zero + transfer learning (VGG/ResNet) com metricas (acc, prec, recall, F1, conf matrix).
- Prototipo de apresentacao (notebook interativo ou Flask simples; opcional mobile como extra).
- Relatorio curto (1-2 pgs) descrevendo pipeline, escolhas e metricas. Extras: etica/fairness e integracao mobile.

## Estrutura proposta
- `FASE4/notebooks/` - notebooks principais da fase.
- `FASE4/data/raw/` - dataset bruto (ex.: NIH Chest X-Ray ou outro publico).
- `FASE4/data/processed/` - dados transformados (tensors/imagens normalizadas).
- `FASE4/app/` - prototipo de interface (Flask ou outro).
- `FASE4/reports/` - relatorios curtos e metricas salvas.

## Grupo (mesmo da Fase 3)
- Caio Rodrigues Castro
- Felipe Soares Nascimento
- Fernando Miranda Segregio
- Mario Roberto Silva de Almeida
- Wellington Nascimento de Brito

Tutor: Leonardo Ruiz Orabona | Coordenador: Andre Godoi

## Setup rapido
```bash
python -m venv .venv
.\\.venv\\Scripts\\activate
pip install --upgrade pip
# PyTorch nightly para Python 3.13 (CPU)
pip install torch==2.10.0.dev20251205+cpu torchvision==0.25.0.dev20251205+cpu torchaudio==2.10.0.dev20251205+cpu --index-url https://download.pytorch.org/whl/nightly/cpu
# Demais deps
pip install scikit-learn matplotlib seaborn pandas opencv-python scikit-image notebook tqdm
```

## Dataset sugerido
- NIH Chest X-Ray (Kaggle) ou similar. Baixe manualmente e coloque em `FASE4/data/raw/chest_xray/`.
- Estrutura esperada para ImageFolder: `class_name/arquivo.png`. Ajuste no notebook se usar outro layout.

## Proximos passos
1) Notebook `phase4_cv.ipynb`: pipeline de pre-processamento + CNN baseline + transfer learning + metricas (rode com `use_fake_data=False` quando o dataset real estiver no caminho).
2) Salvar metricas/prints em `FASE4/reports/` (acc, prec, recall, F1, confusion matrix, curvas).
3) Exportar modelo treinado para `FASE4/app/model.pt` e preencher `CLASS_NAMES` em `FASE4/app/app.py`. Rodar: `flask --app FASE4/app/app run --debug`.
4) Relatorio curto `FASE4/reports/REPORT_PHASE4.md` e (opcional) `FASE4/reports/fairness.md`.
5) (Opcional) Mobile: consumir endpoint Flask/Node para mostrar predicao em React Native.

## Checklist rapido para o professor
- [ ] Dataset em `FASE4/data/raw/...` e notebook salvo apos execucao real (sem FakeData).
- [ ] Metricas e figuras em `FASE4/reports/`.
- [ ] `model.pt` e `CLASS_NAMES` atualizados em `FASE4/app/app.py`.
- [ ] Relatorio(s) em `FASE4/reports/` descrevendo pipeline e resultados.
