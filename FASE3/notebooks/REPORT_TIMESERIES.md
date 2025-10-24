# IR ALÉM 2 — Relatório (Séries Temporais)

## Objetivo

Comparar métodos simples de detecção de anomalias em séries temporais de saúde (BPM, temperatura).

## Metodologia

- Geração de dados sintéticos com picos (BPM=125) e febre (Temp≈38.6°C).
- Métodos avaliados: Z‑score (|z|>3) e MAD (|score|>3.5).
- Visualizações e marcação de anomalias no notebook `notebooks/phase3_time_series.ipynb`.

## Resultados

- Ambos os métodos detectam picos abruptos com boa precisão.
- MAD é mais robusto a outliers e escalares.
- Z‑score é simples e eficiente para séries estáveis.

## Conclusões

Os métodos baselines são adequados para protótipos. Para produção, considerar janelas móveis, sazonalidade e modelos específicos (ARIMA, LSTM, Prophet), além de validação clínica.

