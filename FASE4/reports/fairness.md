# IR Alem 1 - Etica e Fairness (esqueleto)

## Possiveis vieses/limitacoes do dataset
- Desbalanceamento entre classes (ex.: normal vs patologia, sexo, idade).
- Variacao de qualidade/contraste (instituicoes diferentes).
- Padroes etarios/geograficos nao representados.
- Risco de correlacoes espurias (artefatos, marcadores, textos na imagem).
- Contagem real (chest_xray Kaggle): train NORMAL=1342, PNEUMONIA=3876; val 8/8 (balanceado); test NORMAL=234, PNEUMONIA=390. Treino e desbalanceado a favor de PNEUMONIA.

## Metricas sugeridas
- Distribuicao de classes no train/val/test.
- Precision/recall/F1 por classe.
- TPR/FPR por subgrupos (se metadados existirem: sexo, idade, equipamento).
- Calibration (opc.).

## Mitigacao recomendada
- Rebalancear via weighted loss ou oversampling.
- Data augmentation controlado (rotacao leve, flip horizontal, jitter de brilho/contraste).
- Remover textos/artefatos com cropping ou masking.
- Separar splits por paciente (evitar leakage) se IDs existirem.
- Ajustar weighted loss usando inverso da frequencia: peso NORMAL ≈ 0.26, PNEUMONIA ≈ 0.74 no train. Alternativa: sampler balanceado.

## Plano de execucao no repo
- Adicionar notebook ou celulas extras no `phase4_cv.ipynb` para:
  - Mostrar contagem por classe.
  - Calcular metrics por classe/subgrupo (quando metadados permitirem).
  - Comparar baseline vs transfer learning em fairness metrics.
- Registrar conclusoes e limitacoes aqui e linkar no relatorio final.
