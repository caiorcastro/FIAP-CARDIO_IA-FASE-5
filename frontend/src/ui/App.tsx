import { useEffect, useMemo, useRef, useState } from 'react'

type AssistantMode = 'LOCAL' | 'WATSON' | 'INDISPONÍVEL'

type AppConfig = {
  watson_console_url?: string | null
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

const SUGGESTIONS: Array<{ label: string; text: string }> = [
  { label: 'Agendar consulta', text: 'Quero agendar uma consulta' },
  { label: 'Dor no peito', text: 'Estou com dor no peito' },
  { label: 'Pressão alta', text: 'O que é pressão alta?' },
]

export default function App() {
  const [mode, setMode] = useState<AssistantMode>('INDISPONÍVEL')
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

            <div className="fineprint">
              Este protótipo não substitui orientação médica. Se você estiver em risco imediato, ligue 192 (SAMU).
            </div>
          </div>
        </main>
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
                    A conversa “puxa” o raciocínio de triagem e organização clínica (Fase 2), o contexto de monitoramento
                    contínuo (Fase 3) e a ideia de apoio ao diagnóstico por imagem (Fase 4), consolidando a experiência do paciente.
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
