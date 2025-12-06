# CardioIA - Fase 4 (Visao Computacional)

Resumo rapido para avaliacao da fase.

## Pedido da fase
- Pre-processar imagens medicas simuladas.
- Treinar CNN simples (do zero) e transfer learning (ex.: ResNet/VGG).
- Apresentar metricas (acc, precision, recall, F1, matriz de confusao).
- Prototipo de apresentacao (notebook interativo ou app simples/Flask).
- Extras: etica/fairness (IR Alem 1) e integracao mobile (IR Alem 2).

## Grupo (mesmo da Fase 3)
- Caio Rodrigues Castro
- Felipe Soares Nascimento
- Fernando Miranda Segregio
- Mario Roberto Silva de Almeida
- Wellington Nascimento de Brito

Tutor: Leonardo Ruiz Orabona | Coordenador: Andre Godoi

## Como foi executado (setup)
- Ambiente: Python 3.13, PyTorch nightly CPU (2.10.0.dev20251205), torchvision, torchaudio, scikit-learn, pandas, matplotlib, seaborn, opencv-python, scikit-image, notebook, tqdm, flask.
- Venv: `.venv` (ativar com `.\\.venv\\Scripts\\activate`).
- Estrutura: `FASE4/` com `notebooks/`, `data/raw|processed/`, `app/`, `reports/`.
- Notebook principal: `FASE4/notebooks/phase4_cv.ipynb` com pipeline de transforms, dataloaders, CNN baseline e stub de transfer learning.
- Prototipo Flask: `FASE4/app/app.py` com endpoints `/health` e `/predict`; espera `model.pt` e `CLASS_NAMES` preenchidos apos treino.
- Dataset real (Kaggle chest_xray) organizado em `FASE4/data/raw/chest_xray/{train,val,test}` com `NORMAL/` e `PNEUMONIA/`.
- CNN baseline (SmallCNN) treinada rapidamente em subset real: metricas em `FASE4/reports/metrics.json` (val_acc ~0.50 neste subset curto).
- Transfer Learning (ResNet18 com pesos DEFAULT) treinado em subset (train=200, val=16, 1 epoch, img_size=128): metricas em `FASE4/reports/metrics_transfer.json` (val_acc ~0.688, F1 macro ~0.676), figuras `confusion_matrix_transfer.png` e `training_curves_transfer.png`. Modelo salvo em `FASE4/app/model.pt` (usa `CLASS_NAMES = ["NORMAL", "PNEUMONIA"]`).

## Resultados atuais (para avaliacao)
- CNN baseline (SmallCNN, subset rapido): ver `metrics.json` (val_acc ~0.50).
- Transfer Learning ResNet18 (weights DEFAULT), subset maior (train=800, val=16, 3 epocas, img 128, bs=32): `metrics_transfer.json` com val_acc ~0.875, F1 macro ~0.875; figuras `confusion_matrix_transfer.png`, `training_curves_transfer.png`; modelo salvo em `FASE4/app/model.pt`.
- Contagem de classes: train NORMAL=1342, PNEUMONIA=3876 (desbalanceado); val 8/8; test 234/390. Ver `fairness.md` para sugestao de weighted loss/oversampling.
- Evidencia `/predict`: `FASE4/reports/predict_example.json` (imagem real de teste NORMAL; retorno top_class=normal, probs ~0.70/0.30).

## O que ainda poderia subir (opcional se houver tempo)
1) Rodar mais epocas/dados completos para consolidar metricas finais (atualizar artifacts).
2) Salvar notebook executado (print ou checkpoint) e referenciar no README/report.
3) Adicionar evidencia do Flask (`/predict`) com imagem real no relatório ou README.

## Como rodar rapidamente
```bash
.\\.venv\\Scripts\\activate
# Treino/analise:
jupyter notebook FASE4/notebooks/phase4_cv.ipynb
# Servir modelo apos exportar:
flask --app FASE4/app/app run --debug
# Teste de API (PowerShell):
curl -F \"file=@exemplo.jpg\" http://127.0.0.1:5000/predict
```

## Entregaveis esperados ao final
- Notebook salvo com execucao real (dataset nao-fake).
- Metricas e figuras em `FASE4/reports/`.
- `model.pt` + `CLASS_NAMES` configurados no Flask.
- Relatorio curto desta fase e (opcional) fairness/mobile como anexos.
