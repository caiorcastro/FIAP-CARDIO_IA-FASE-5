import { useEffect, useMemo, useRef, useState } from 'react'

type AssistantMode = 'LOCAL' | 'WATSON' | 'INDISPONÍVEL'
type TabKey = 'chat' | 'organizer' | 'monitor' | 'image'

type AppConfig = {
  watson_console_url?: string | null
}

type ClinicalExtractResponse = {
  source: 'gemini' | 'local'
  summary: string
  structured: Record<string, any>
  triage: Record<string, any>
}

type MonitorLogsResponse = {
  logs: Array<Record<string, any>>
}

type ChatMsg = {
  id: string
  role: 'user' | 'assistant'
  text: string
  ts: number
}

function uuid() {
  return crypto.randomUUID()
}

function formatTime(ts: number) {
  const d = new Date(ts)
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

async function fetchStatus(): Promise<AssistantMode> {
  try {
    const res = await fetch('/api/status')
    const data = await res.json()
    const impl = String(data?.assistant || '').toLowerCase()
    if (impl === 'local' || impl === 'mock') return 'LOCAL'
    if (impl === 'watson') return 'WATSON'
    return 'INDISPONÍVEL'
  } catch {
    return 'INDISPONÍVEL'
  }
}

async function sendToAssistant(message: string, userId: string) {
  const res = await fetch('/api/message', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, user_id: userId }),
  })
  const payload = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(payload?.error || 'Falha ao enviar mensagem')
  return payload as { response: string }
}

async function extractClinical(text: string) {
  const res = await fetch('/api/clinical/extract', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  })
  const payload = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(payload?.error || 'Falha ao extrair informacoes clinicas')
  return payload as ClinicalExtractResponse
}

async function fetchMonitorLogs() {
  const res = await fetch('/api/monitor/logs')
  const payload = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(payload?.error || 'Falha ao carregar logs')
  return payload as MonitorLogsResponse
}

async function runMonitorOnce() {
  const res = await fetch('/api/monitor/run_once', { method: 'POST' })
  const payload = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(payload?.error || 'Falha ao rodar ciclo do robô')
  return payload as { ok?: boolean; error?: string; logs?: Array<Record<string, any>> }
}

async function checkVitals(temp: string, bpm: string) {
  const res = await fetch('/api/phase3/vitals', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      ts: Math.floor(Date.now() / 1000),
      temp: temp ? Number(temp) : null,
      bpm: bpm ? Number(bpm) : null,
    }),
  })
  const payload = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(payload?.error || 'Falha ao avaliar vitais')
  return payload as { source: string; result: any }
}

async function fetchPhase4Health() {
  const res = await fetch('/api/phase4/health')
  const payload = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(payload?.error || 'Falha ao consultar Fase 4')
  return payload as { available: boolean; health: any }
}

const SUGGESTIONS: Array<{ label: string; text: string }> = [
  { label: 'Agendar consulta', text: 'Quero agendar uma consulta' },
  { label: 'Dor no peito', text: 'Estou com dor no peito' },
  { label: 'Pressão alta', text: 'O que é pressão alta?' },
]

export default function App() {
  const [mode, setMode] = useState<AssistantMode>('INDISPONÍVEL')
  const [tab, setTab] = useState<TabKey>('chat')
  const [busy, setBusy] = useState(false)
  const [input, setInput] = useState('')
  const [aboutOpen, setAboutOpen] = useState(false)
  const [cfg, setCfg] = useState<AppConfig>({})
  const [msgs, setMsgs] = useState<ChatMsg[]>(() => [
    {
      id: uuid(),
      role: 'assistant',
      ts: Date.now(),
      text:
        'Olá. Eu sou o CardioIA.\n\nPosso ajudar com atendimento inicial, triagem de sinais de alerta e pré-agendamento de consulta.\n\nComo posso te ajudar agora?',
    },
  ])

  const userId = useMemo(() => 'user_' + uuid(), [])
  const listRef = useRef<HTMLDivElement>(null)

  const [extractText, setExtractText] = useState('')
  const [extractBusy, setExtractBusy] = useState(false)
  const [extractResult, setExtractResult] = useState<ClinicalExtractResponse | null>(null)
  const [extractError, setExtractError] = useState<string | null>(null)

  const [logsBusy, setLogsBusy] = useState(false)
  const [logs, setLogs] = useState<Array<Record<string, any>>>([])
  const [logsError, setLogsError] = useState<string | null>(null)

  const [temp, setTemp] = useState('')
  const [bpm, setBpm] = useState('')
  const [vitalsBusy, setVitalsBusy] = useState(false)
  const [vitalsResult, setVitalsResult] = useState<{ source: string; result: any } | null>(null)
  const [vitalsError, setVitalsError] = useState<string | null>(null)

  const [phase4Busy, setPhase4Busy] = useState(false)
  const [phase4, setPhase4] = useState<{ available: boolean; health: any } | null>(null)
  const [phase4Error, setPhase4Error] = useState<string | null>(null)

  useEffect(() => {
    fetchStatus().then(setMode)
    fetch('/api/config')
      .then((r) => r.json())
      .then((d) => setCfg({ watson_console_url: d?.watson_console_url ?? null }))
      .catch(() => setCfg({}))
  }, [])

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: 'smooth' })
  }, [msgs.length])

  useEffect(() => {
    if (tab !== 'monitor') return
    setLogsBusy(true)
    setLogsError(null)
    fetchMonitorLogs()
      .then((d) => setLogs(Array.isArray(d.logs) ? d.logs : []))
      .catch((e: any) => setLogsError(e?.message || 'Falha ao carregar logs'))
      .finally(() => setLogsBusy(false))
  }, [tab])

  useEffect(() => {
    if (tab !== 'image') return
    setPhase4Busy(true)
    setPhase4Error(null)
    fetchPhase4Health()
      .then(setPhase4)
      .catch((e: any) => setPhase4Error(e?.message || 'Falha ao consultar Fase 4'))
      .finally(() => setPhase4Busy(false))
  }, [tab])

  async function onSend(text?: string) {
    const msg = (text ?? input).trim()
    if (!msg || busy) return

    setInput('')
    setBusy(true)

    const now = Date.now()
    setMsgs((m) => [...m, { id: uuid(), role: 'user', text: msg, ts: now }])

    // typing placeholder
    const typingId = uuid()
    setMsgs((m) => [...m, { id: typingId, role: 'assistant', text: 'Digitando...', ts: Date.now() }])

    try {
      const data = await sendToAssistant(msg, userId)
      setMsgs((m) =>
        m.map((x) => (x.id === typingId ? { ...x, text: String(data.response || '').trim() || 'Sem resposta.' } : x)),
      )
      setMode(await fetchStatus())
    } catch (e: any) {
      setMsgs((m) =>
        m.map((x) => (x.id === typingId ? { ...x, text: `Erro: ${e?.message || 'falha de comunicação'}` } : x)),
      )
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="page">
      <div className="shell">
        <header className="top">
          <div className="brand">
            <div className="mark" aria-hidden="true">
              <span />
            </div>
            <div className="brandText">
              <div className="titleRow">
                <h1>CardioIA</h1>
                <span className={`pill pill--${mode.toLowerCase()}`}>Modo: {mode}</span>
              </div>
              <p>Assistente cardiológico conversacional (FIAP)</p>
            </div>
          </div>

          <div className="topActions">
            <button className="ghostBtn" onClick={() => setAboutOpen(true)} type="button">
              Sobre
            </button>
            <a
              className="ghostBtn"
              href={cfg?.watson_console_url || 'https://cloud.ibm.com/catalog/services/watson-assistant'}
              target="_blank"
              rel="noreferrer"
              title="Abrir Watson Assistant no IBM Cloud"
            >
              Watson IBM
            </a>
          </div>
        </header>

        <nav className="tabs" aria-label="Navegação">
          <button className={`tab ${tab === 'chat' ? 'tab--active' : ''}`} onClick={() => setTab('chat')} type="button">
            Conversa
          </button>
          <button
            className={`tab ${tab === 'organizer' ? 'tab--active' : ''}`}
            onClick={() => setTab('organizer')}
            type="button"
          >
            Organizar relato
          </button>
          <button
            className={`tab ${tab === 'monitor' ? 'tab--active' : ''}`}
            onClick={() => setTab('monitor')}
            type="button"
          >
            Monitoramento
          </button>
          <button
            className={`tab ${tab === 'image' ? 'tab--active' : ''}`}
            onClick={() => setTab('image')}
            type="button"
          >
            Imagem (Fase 4)
          </button>
        </nav>

        {tab === 'chat' ? (
          <main className="chat">
            <div className="messages" ref={listRef} role="log" aria-live="polite">
              {msgs.map((m) => (
                <div key={m.id} className={`bubble bubble--${m.role}`}>
                  <div className="bubbleInner">
                    <div className="bubbleText" style={{ whiteSpace: 'pre-wrap' }}>
                      {m.text}
                    </div>
                    <div className="bubbleMeta">{formatTime(m.ts)}</div>
                  </div>
                </div>
              ))}
            </div>

            <div className="composer">
              <div className="chips" aria-label="Sugestões rápidas">
                {SUGGESTIONS.map((s) => (
                  <button key={s.label} className="chip" onClick={() => onSend(s.text)} disabled={busy}>
                    {s.label}
                  </button>
                ))}
              </div>

              <div className="row">
                <textarea
                  className="input"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Digite sua mensagem..."
                  rows={2}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault()
                      onSend()
                    }
                  }}
                />
                <button className="send" onClick={() => onSend()} disabled={busy || !input.trim()}>
                  Enviar
                </button>
              </div>
            </div>
          </main>
        ) : null}

        {tab === 'organizer' ? (
          <main className="pane">
            <section className="hero">
              <div className="heroText">
                <div className="kicker">Ir Além 1</div>
                <h2>Extração de informações clínicas</h2>
                <p>
                  Cole um relato em texto livre e o sistema devolve uma saída <strong>estruturada</strong> (JSON) com triagem
                  reaproveitando a Fase 2. Se houver chave do Gemini, usa GenAI; se não, faz fallback local.
                </p>
              </div>
              <div className="heroCard">
                <div className="stat">
                  <div className="statLabel">Fonte</div>
                  <div className="statValue">{extractResult?.source?.toUpperCase?.() || 'LOCAL/GEMINI'}</div>
                </div>
                <div className="stat">
                  <div className="statLabel">Saída</div>
                  <div className="statValue">JSON</div>
                </div>
              </div>
            </section>

            <section className="grid2">
              <div className="card">
                <div className="cardTop">
                  <h3>Relato do paciente</h3>
                  <button
                    className="ghostBtn"
                    type="button"
                    onClick={() => {
                      const lastUser = [...msgs].reverse().find((m) => m.role === 'user')?.text
                      if (lastUser) setExtractText(lastUser)
                    }}
                    title="Usar a última mensagem enviada no chat"
                  >
                    Usar última msg
                  </button>
                </div>
                <textarea
                  className="input input--tall"
                  value={extractText}
                  onChange={(e) => setExtractText(e.target.value)}
                  placeholder="Ex: Estou com dor no peito há 2 horas, pressão 150/95, muita ansiedade..."
                  rows={8}
                />
                <div className="cardActions">
                  <button
                    className="send"
                    type="button"
                    disabled={extractBusy || !extractText.trim()}
                    onClick={async () => {
                      setExtractBusy(true)
                      setExtractError(null)
                      setExtractResult(null)
                      try {
                        const r = await extractClinical(extractText)
                        setExtractResult(r)
                      } catch (e: any) {
                        setExtractError(e?.message || 'Falha na extração')
                      } finally {
                        setExtractBusy(false)
                      }
                    }}
                  >
                    {extractBusy ? 'Extraindo...' : 'Extrair'}
                  </button>
                  <button
                    className="ghostBtn"
                    type="button"
                    onClick={() => {
                      setExtractText('')
                      setExtractError(null)
                      setExtractResult(null)
                    }}
                  >
                    Limpar
                  </button>
                </div>
                {extractError ? <div className="alert alert--bad">Erro: {extractError}</div> : null}
              </div>

              <div className="card">
                <h3>Resultado estruturado</h3>
                {extractResult ? (
                  <>
                    <div className="alert alert--ok">{extractResult.summary}</div>
                    <div className="subgrid">
                      <div className="mini">
                        <div className="miniLabel">Triagem</div>
                        <pre className="mono">{JSON.stringify(extractResult.triage, null, 2)}</pre>
                      </div>
                      <div className="mini">
                        <div className="miniLabel">JSON</div>
                        <pre className="mono">{JSON.stringify(extractResult.structured, null, 2)}</pre>
                      </div>
                    </div>
                  </>
                ) : (
                  <p className="muted">Nenhum resultado ainda. Clique em "Extrair".</p>
                )}
              </div>
            </section>
          </main>
        ) : null}

        {tab === 'monitor' ? (
          <main className="pane">
            <section className="hero">
              <div className="heroText">
                <div className="kicker">Ir Além 2 + Fase 3</div>
                <h2>Monitoramento e rastreabilidade</h2>
                <p>
                  Aqui o protótipo junta automação (RPA) com dados híbridos (SQLite + JSON) e reaproveita o conceito de
                  alertas da Fase 3.
                </p>
              </div>
              <div className="heroCard">
                <button
                  className="ghostBtn"
                  type="button"
                  disabled={logsBusy}
                  onClick={async () => {
                    setLogsBusy(true)
                    setLogsError(null)
                    try {
                      const d = await fetchMonitorLogs()
                      setLogs(Array.isArray(d.logs) ? d.logs : [])
                    } catch (e: any) {
                      setLogsError(e?.message || 'Falha ao carregar logs')
                    } finally {
                      setLogsBusy(false)
                    }
                  }}
                >
                  {logsBusy ? 'Atualizando...' : 'Atualizar logs'}
                </button>
                <button
                  className="send"
                  type="button"
                  disabled={logsBusy}
                  onClick={async () => {
                    setLogsBusy(true)
                    setLogsError(null)
                    try {
                      const d = await runMonitorOnce()
                      setLogs(Array.isArray(d.logs) ? d.logs : [])
                    } catch (e: any) {
                      setLogsError(e?.message || 'Falha ao rodar o robô')
                    } finally {
                      setLogsBusy(false)
                    }
                  }}
                >
                  Rodar 1 ciclo do robô
                </button>
              </div>
            </section>

            <section className="grid2">
              <div className="card">
                <h3>Logs do robô (NoSQL em JSON)</h3>
                {logsError ? <div className="alert alert--bad">Erro: {logsError}</div> : null}
                {logs.length ? (
                  <div className="logList">
                    {logs.slice().reverse().slice(0, 20).map((l, idx) => (
                      <div className="logItem" key={idx}>
                        <div className="logTop">
                          <div className="logTitle">{String(l.patient || 'Paciente')}</div>
                          <div className="logMeta">{String(l.timestamp || '')}</div>
                        </div>
                        <div className="logBody">
                          <div className="tag">{String(l.status || 'STATUS')}</div>
                          <div className="muted small">
                            Vitals: {String(l?.vitals?.bp || '-')} | {String(l?.vitals?.hr || '-')}{' '}
                            {l?.vitals?.hr ? 'bpm' : ''}
                          </div>
                          {l.ai_analysis ? <div className="muted">{String(l.ai_analysis)}</div> : null}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="muted">
                    Nenhum log ainda. Clique em "Rodar 1 ciclo do robô" (o banco SQLite e os logs serão criados em
                    `automation/data/`).
                  </p>
                )}
              </div>

              <div className="card">
                <h3>Simulador de vitais (regra da Fase 3)</h3>
                <p className="muted">
                  Avalia risco com a regra simples (bpm&gt;120, temp&gt;38). Se `PHASE3_ALERTS_URL` estiver configurada, o
                  backend tenta chamar o serviço externo; se não, aplica a regra local equivalente.
                </p>
                <div className="formGrid">
                  <label className="field">
                    <span>Temperatura (C)</span>
                    <input className="text" value={temp} onChange={(e) => setTemp(e.target.value)} placeholder="Ex: 37.2" />
                  </label>
                  <label className="field">
                    <span>BPM</span>
                    <input className="text" value={bpm} onChange={(e) => setBpm(e.target.value)} placeholder="Ex: 130" />
                  </label>
                </div>
                <div className="cardActions">
                  <button
                    className="send"
                    type="button"
                    disabled={vitalsBusy || (!temp.trim() && !bpm.trim())}
                    onClick={async () => {
                      setVitalsBusy(true)
                      setVitalsError(null)
                      setVitalsResult(null)
                      try {
                        setVitalsResult(await checkVitals(temp, bpm))
                      } catch (e: any) {
                        setVitalsError(e?.message || 'Falha ao avaliar vitais')
                      } finally {
                        setVitalsBusy(false)
                      }
                    }}
                  >
                    {vitalsBusy ? 'Avaliando...' : 'Avaliar'}
                  </button>
                  <button
                    className="ghostBtn"
                    type="button"
                    onClick={() => {
                      setTemp('')
                      setBpm('')
                      setVitalsError(null)
                      setVitalsResult(null)
                    }}
                  >
                    Limpar
                  </button>
                </div>
                {vitalsError ? <div className="alert alert--bad">Erro: {vitalsError}</div> : null}
                {vitalsResult ? (
                  <div className="alert alert--ok">
                    <div className="small muted">Fonte: {vitalsResult.source}</div>
                    <pre className="mono">{JSON.stringify(vitalsResult.result, null, 2)}</pre>
                  </div>
                ) : null}
              </div>
            </section>
          </main>
        ) : null}

        {tab === 'image' ? (
          <main className="pane">
            <section className="hero">
              <div className="heroText">
                <div className="kicker">Fase 4</div>
                <h2>Apoio por imagem (opcional)</h2>
                <p>
                  A Fase 4 vive como um serviço separado (Flask + PyTorch). A Fase 5 consegue detectar se o serviço está
                  disponível via `/health`.
                </p>
              </div>
              <div className="heroCard">
                <div className="stat">
                  <div className="statLabel">Status</div>
                  <div className="statValue">{phase4Busy ? '...' : phase4?.available ? 'ONLINE' : 'OFFLINE'}</div>
                </div>
                <button
                  className="ghostBtn"
                  type="button"
                  disabled={phase4Busy}
                  onClick={async () => {
                    setPhase4Busy(true)
                    setPhase4Error(null)
                    try {
                      setPhase4(await fetchPhase4Health())
                    } catch (e: any) {
                      setPhase4Error(e?.message || 'Falha ao consultar Fase 4')
                    } finally {
                      setPhase4Busy(false)
                    }
                  }}
                >
                  Atualizar
                </button>
              </div>
            </section>

            <section className="grid2">
              <div className="card">
                <h3>Como habilitar</h3>
                <p className="muted">
                  1) Inicie o serviço da Fase 4 em outro terminal (ver `FASES ANTERIORES/FASE4/app/app.py`).<br />
                  2) Configure `PHASE4_CV_URL` no `.env` (ex: `http://127.0.0.1:5001`).<br />
                  3) Volte aqui e clique em "Atualizar".
                </p>
                {phase4Error ? <div className="alert alert--bad">Erro: {phase4Error}</div> : null}
              </div>

              <div className="card">
                <h3>Resposta do /health</h3>
                {phase4?.health ? <pre className="mono">{JSON.stringify(phase4.health, null, 2)}</pre> : <p className="muted">Sem dados.</p>}
              </div>
            </section>
          </main>
        ) : null}
      </div>

      {aboutOpen ? (
        <div className="modalOverlay" role="dialog" aria-modal="true" aria-label="Sobre o CardioIA">
          <div className="modalCard">
            <div className="modalTop">
              <div className="modalTitle">
                <div className="modalKicker">CardioIA</div>
                <h2>Fase 5: Experiência do Paciente</h2>
                <p>
                  Protótipo conversacional para <strong>atendimento inicial</strong>, <strong>triagem</strong> e{' '}
                  <strong>pré-agendamento</strong>, integrando <strong>Flask</strong> e <strong>IBM Watson Assistant</strong>.
                </p>
              </div>
              <button className="closeBtn" onClick={() => setAboutOpen(false)} type="button" aria-label="Fechar">
                Fechar
              </button>
            </div>

            <div className="modalBody">
              <div className="aboutGrid">
                <div className="aboutBox">
                  <h3>Arquitetura</h3>
                  <p>Usuário → Web (React) → API (Flask) → Watson (V2)</p>
                  <pre className="mono">
{`UI  →  POST /api/message
API →  Watson Assistant V2
API →  resposta (texto + metadados)`}
                  </pre>
                </div>

                <div className="aboutBox">
                  <h3>Como a Fase 5 se conecta às anteriores</h3>
                  <p>
                    A entrega integra na própria aplicação: triagem (Fase 2), monitoramento/alertas (Fase 3), e um ponto de
                    extensão para análise por imagem (Fase 4), consolidando a experiência do paciente.
                  </p>
                </div>

                <div className="aboutBox">
                  <h3>Para o vídeo</h3>
                  <p>
                    Você pode demonstrar em <strong>modo Watson</strong> (publicado) e em <strong>modo local</strong> (offline),
                    garantindo que a banca consiga testar mesmo sem credenciais.
                  </p>
                  <div className="links">
                    <a className="link" href="/docs/fase5/relatorio_conversacional.pdf" target="_blank" rel="noreferrer">
                      Relatório (PDF)
                    </a>
                    <a className="link" href="/docs/fase5/checklist_requisitos.md" target="_blank" rel="noreferrer">
                      Checklist (MD)
                    </a>
                    <a className="link" href="/docs/anteriores/REPORT-DE-AVAN%C3%87O.MD" target="_blank" rel="noreferrer">
                      Fases anteriores (MD)
                    </a>
                    <a className="link" href="/docs/root/CONTRIBUTORS.md" target="_blank" rel="noreferrer">
                      Integrantes (MD)
                    </a>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <button className="modalBackdrop" onClick={() => setAboutOpen(false)} aria-label="Fechar" />
        </div>
      ) : null}
    </div>
  )
}
