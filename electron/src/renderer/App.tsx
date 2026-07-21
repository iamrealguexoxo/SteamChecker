import { useMemo, useState, useCallback } from 'react'
import { AnimatePresence, motion } from 'motion/react'
import {
  Search, CheckCircle2, AlertTriangle, XCircle, Copy, Check, ExternalLink,
  Loader2, Boxes, GitCompareArrows, Sparkles, HelpCircle, Trash2,
} from 'lucide-react'
import {
  parseWorkshopIds, parseModIds, compareModIds, workshopUrl,
  type CheckResult, type CheckStatus, type Comparison,
} from './lib/checker'

const DELAY_MS = 500 // throttle between requests (Python used 0.6s)

type Tone = 'ok' | 'warn' | 'bad'
const TONE: Record<Tone, { color: string; bg: string; border: string }> = {
  ok: { color: '#34d399', bg: 'rgba(52,211,153,0.10)', border: 'rgba(52,211,153,0.28)' },
  warn: { color: '#f59e0b', bg: 'rgba(245,158,11,0.10)', border: 'rgba(245,158,11,0.28)' },
  bad: { color: '#f87171', bg: 'rgba(248,113,113,0.10)', border: 'rgba(248,113,113,0.28)' },
}

function statusMeta(r: CheckResult): { tone: Tone; label: string; Icon: typeof CheckCircle2 } {
  if (r.status === 'OK') {
    return r.warning
      ? { tone: 'warn', label: 'Warnung', Icon: AlertTriangle }
      : { tone: 'ok', label: 'OK', Icon: CheckCircle2 }
  }
  if (r.status === 'NO_TITLE') return { tone: 'warn', label: 'Kein Titel', Icon: AlertTriangle }
  if (r.status === 'GELÖSCHT') return { tone: 'bad', label: 'Gelöscht', Icon: XCircle }
  return { tone: 'bad', label: r.status === 'TIMEOUT' ? 'Timeout' : 'Fehler', Icon: XCircle }
}

function warningLabel(w: string): string {
  if (w.includes('OUTDATE')) return 'Veraltet / Outdated'
  if (w.includes('VERSION')) return 'Andere Version (B42)'
  return w
}

/* ─────────────────────────────────────────────────────────────── */

function CopyButton({ text, label = 'Kopieren' }: { text: string; label?: string }) {
  const [done, setDone] = useState(false)
  return (
    <button
      onClick={() => {
        navigator.clipboard.writeText(text).then(() => {
          setDone(true)
          setTimeout(() => setDone(false), 1400)
        })
      }}
      className="no-drag inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition-colors"
      style={{ background: done ? 'rgba(52,211,153,0.15)' : '#222227', color: done ? '#34d399' : '#e7ecf3' }}
    >
      {done ? <Check size={13} /> : <Copy size={13} />}
      {done ? 'Kopiert' : label}
    </button>
  )
}

function Pill({ children, tone }: { children: React.ReactNode; tone?: Tone }) {
  const t = tone ? TONE[tone] : { color: '#66c0f4', bg: 'rgba(102,192,244,0.10)', border: 'rgba(102,192,244,0.25)' }
  return (
    <span
      className="mono inline-flex items-center rounded-md px-2 py-0.5 text-[11px] font-medium"
      style={{ color: t.color, background: t.bg, border: `1px solid ${t.border}` }}
    >
      {children}
    </span>
  )
}

/* ─────────────────────────────────────────────────────────────── */

function ResultRow({ r, index }: { r: CheckResult; index: number }) {
  const meta = statusMeta(r)
  const t = TONE[meta.tone]
  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.22, delay: Math.min(index * 0.01, 0.15) }}
      className="rounded-[0.9rem] border p-3"
      style={{ background: '#19191d', borderColor: 'var(--border)' }}
    >
      <div className="flex items-start gap-3">
        <div
          className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg"
          style={{ background: t.bg, color: t.color }}
        >
          <meta.Icon size={17} />
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-[13px] font-semibold" style={{ color: t.color }}>{meta.label}</span>
            <button
              onClick={() => window.api.openExternal(workshopUrl(r.id))}
              className="no-drag mono inline-flex items-center gap-1 text-[11px] text-[var(--muted)] transition-colors hover:text-[#66c0f4]"
              title="Auf Steam öffnen"
            >
              {r.id}<ExternalLink size={11} />
            </button>
          </div>

          {r.title && (
            <p className="mt-1 truncate text-sm text-[var(--text)]" title={r.title}>{r.title}</p>
          )}
          {r.error && <p className="mt-1 text-xs text-[#f87171]">{r.error}</p>}
          {r.status === 'NO_TITLE' && (
            <p className="mt-1 text-xs text-[var(--muted)]">Titel nicht lesbar — evtl. privat oder gelöscht.</p>
          )}

          <div className="mt-2 flex flex-wrap items-center gap-1.5">
            {r.warning && <Pill tone="warn">{warningLabel(r.warning)}</Pill>}
            {r.modIds?.map((m) => <Pill key={m}>{m}</Pill>)}
          </div>
        </div>
      </div>
    </motion.div>
  )
}

/* ─────────────────────────────────────────────────────────────── */

export default function App() {
  const [rawInput, setRawInput] = useState('')
  const [results, setResults] = useState<CheckResult[]>([])
  const [checking, setChecking] = useState(false)
  const [progress, setProgress] = useState({ done: 0, total: 0 })

  const [configInput, setConfigInput] = useState('')
  const [comparison, setComparison] = useState<Comparison | null>(null)

  const parsedIds = useMemo(() => parseWorkshopIds(rawInput), [rawInput])

  const runCheck = useCallback(async () => {
    const ids = parseWorkshopIds(rawInput)
    if (!ids.length || checking) return
    setChecking(true)
    setResults([])
    setComparison(null)
    setProgress({ done: 0, total: ids.length })

    const collected: CheckResult[] = []
    for (let i = 0; i < ids.length; i++) {
      try {
        const res = await window.api.check(ids[i])
        collected.push(res)
      } catch (e) {
        collected.push({ id: ids[i], status: 'FEHLER', title: null, warning: null, error: String(e), modIds: null })
      }
      setResults([...collected])
      setProgress({ done: i + 1, total: ids.length })
      if (i < ids.length - 1) await new Promise((res) => setTimeout(res, DELAY_MS))
    }
    setChecking(false)
  }, [rawInput, checking])

  const summary = useMemo(() => {
    let ok = 0, warn = 0, bad = 0
    for (const r of results) {
      const tone = statusMeta(r).tone
      if (tone === 'ok') ok++
      else if (tone === 'warn') warn++
      else bad++
    }
    return { ok, warn, bad }
  }, [results])

  // "Clean list" = only items that are OK AND carry no warning.
  const { cleanIds, removedCount } = useMemo(() => {
    const clean: string[] = []
    let removed = 0
    for (const r of results) {
      if (r.status === 'OK' && !r.warning) clean.push(r.id)
      else removed++
    }
    return { cleanIds: clean, removedCount: removed }
  }, [results])

  const hasModIds = useMemo(() => results.some((r) => r.modIds && r.modIds.length), [results])

  const runCompare = useCallback(() => {
    const cfg = parseModIds(configInput)
    if (!cfg.length) { setComparison(null); return }
    setComparison(compareModIds(cfg, results))
  }, [configInput, results])

  const pct = progress.total ? Math.round((progress.done / progress.total) * 100) : 0

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <header className="drag-region relative shrink-0 px-6 pb-4 pt-[26px]">
        <div className="flex items-center gap-3 pl-16">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl" style={{ background: 'rgba(102,192,244,0.12)', color: '#66c0f4' }}>
            <Boxes size={19} />
          </div>
          <div>
            <h1 className="text-[15px] font-semibold leading-tight">SteamChecker</h1>
            <p className="text-[11px] text-[var(--muted)]">Project Zomboid · Workshop-Prüfer</p>
          </div>
        </div>
        <div className="header-accent absolute inset-x-6 bottom-0 h-px" />
      </header>

      {/* Scroll body */}
      <div className="min-h-0 flex-1 overflow-y-auto px-6 pb-8">
        {/* Input card */}
        <section className="mt-3 rounded-[0.9rem] border p-4" style={{ background: '#141416', borderColor: 'var(--border)' }}>
          <label className="flex items-center gap-2 text-xs font-medium text-[var(--muted)]">
            <Search size={13} /> Workshop-IDs (getrennt mit ; )
          </label>
          <textarea
            value={rawInput}
            onChange={(e) => setRawInput(e.target.value)}
            placeholder="2709866494;3445949422;3445362877"
            spellCheck={false}
            rows={3}
            className="no-drag mono mt-2 w-full resize-none rounded-lg border bg-[#0a0a0c] p-3 text-sm text-[var(--text)] outline-none transition-colors placeholder:text-[#4a4a52] focus:border-[#66c0f4]/50"
            style={{ borderColor: 'var(--border)' }}
          />
          <div className="mt-3 flex items-center justify-between gap-3">
            <span className="text-xs text-[var(--muted)]">
              {parsedIds.length > 0 ? `${parsedIds.length} gültige ID${parsedIds.length === 1 ? '' : 's'}` : 'Nur Zahlen zählen'}
            </span>
            <button
              onClick={runCheck}
              disabled={!parsedIds.length || checking}
              className="no-drag inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-semibold transition-all disabled:opacity-40"
              style={{ background: '#66c0f4', color: '#08131c' }}
            >
              {checking ? <Loader2 size={15} className="animate-spin" /> : <Search size={15} />}
              {checking ? `Prüfe… ${progress.done}/${progress.total}` : 'Prüfen'}
            </button>
          </div>

          {checking && (
            <div className="mt-3 h-1 overflow-hidden rounded-full bg-[#0a0a0c]">
              <motion.div className="h-full rounded-full" style={{ background: '#66c0f4' }} animate={{ width: `${pct}%` }} transition={{ duration: 0.3 }} />
            </div>
          )}
        </section>

        {/* Summary */}
        {results.length > 0 && (
          <div className="mt-4 grid grid-cols-3 gap-2">
            {([['ok', 'OK', summary.ok], ['warn', 'Warnung', summary.warn], ['bad', 'Problem', summary.bad]] as const).map(([tone, label, n]) => (
              <div key={tone} className="rounded-[0.9rem] border p-3 text-center" style={{ background: '#19191d', borderColor: TONE[tone].border }}>
                <div className="mono text-xl font-bold" style={{ color: TONE[tone].color }}>{n}</div>
                <div className="text-[11px] text-[var(--muted)]">{label}</div>
              </div>
            ))}
          </div>
        )}

        {/* Results */}
        <div className="mt-3 space-y-2">
          <AnimatePresence initial={false}>
            {results.map((r, i) => <ResultRow key={r.id} r={r} index={i} />)}
          </AnimatePresence>
        </div>

        {/* Clean list */}
        {results.length > 0 && !checking && (
          <section className="mt-4 rounded-[0.9rem] border p-4" style={{ background: '#141416', borderColor: 'var(--border)' }}>
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <Sparkles size={15} className="text-[#34d399]" />
                <h2 className="text-sm font-semibold">Bereinigte Liste</h2>
              </div>
              {cleanIds.length > 0 && <CopyButton text={cleanIds.join(';')} label="Liste kopieren" />}
            </div>
            <p className="mt-1 flex items-center gap-1.5 text-xs text-[var(--muted)]">
              <Trash2 size={12} />
              {removedCount > 0
                ? `${removedCount} Item${removedCount === 1 ? '' : 's'} mit Warnung/Problem entfernt · ${cleanIds.length} verbleiben`
                : 'Alle Items sind sauber'}
            </p>
            {cleanIds.length > 0 && (
              <div className="mono mt-3 max-h-28 overflow-y-auto rounded-lg bg-[#0a0a0c] p-3 text-xs leading-relaxed text-[#34d399]">
                {cleanIds.join(';')}
              </div>
            )}
          </section>
        )}

        {/* Comparison */}
        {hasModIds && !checking && (
          <section className="mt-4 rounded-[0.9rem] border p-4" style={{ background: '#141416', borderColor: 'var(--border)' }}>
            <div className="flex items-center gap-2">
              <GitCompareArrows size={15} className="text-[#66c0f4]" />
              <h2 className="text-sm font-semibold">Mod-IDs abgleichen</h2>
            </div>
            <p className="mt-1 flex items-center gap-1.5 text-xs text-[var(--muted)]">
              <HelpCircle size={12} /> Deine Server-Config Mod-IDs vs. die gefundenen.
            </p>
            <textarea
              value={configInput}
              onChange={(e) => setConfigInput(e.target.value)}
              placeholder="iMeds;SCEEP_Hotwire;GreenHouse"
              spellCheck={false}
              rows={2}
              className="no-drag mono mt-3 w-full resize-none rounded-lg border bg-[#0a0a0c] p-3 text-sm text-[var(--text)] outline-none transition-colors placeholder:text-[#4a4a52] focus:border-[#66c0f4]/50"
              style={{ borderColor: 'var(--border)' }}
            />
            <button
              onClick={runCompare}
              disabled={!configInput.trim()}
              className="no-drag mt-3 inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-semibold transition-all disabled:opacity-40"
              style={{ background: '#222227', color: '#e7ecf3' }}
            >
              <GitCompareArrows size={15} /> Vergleichen
            </button>

            {comparison && (
              <div className="mt-4 space-y-3">
                <div className="grid grid-cols-3 gap-2">
                  {([['ok', 'Vorhanden', comparison.found.length], ['bad', 'Fehlt', comparison.missing.length], ['warn', 'Zusätzlich', comparison.extra.length]] as const).map(([tone, label, n]) => (
                    <div key={label} className="rounded-lg border p-2 text-center" style={{ background: '#19191d', borderColor: TONE[tone].border }}>
                      <div className="mono text-lg font-bold" style={{ color: TONE[tone].color }}>{n}</div>
                      <div className="text-[10px] text-[var(--muted)]">{label}</div>
                    </div>
                  ))}
                </div>

                {comparison.missing.length > 0 && (
                  <div>
                    <p className="mb-1.5 text-xs font-medium text-[#f87171]">Fehlt in den Workshop-Items:</p>
                    <div className="flex flex-wrap gap-1.5">{comparison.missing.map((m) => <Pill key={m} tone="bad">{m}</Pill>)}</div>
                  </div>
                )}
                {comparison.extra.length > 0 && (
                  <div>
                    <p className="mb-1.5 text-xs font-medium text-[#f59e0b]">Zusätzlich gefunden (nicht in Config):</p>
                    <div className="flex flex-wrap gap-1.5">{comparison.extra.map((e) => <Pill key={e.workshopId + e.modId} tone="warn">{e.modId}</Pill>)}</div>
                  </div>
                )}
                {comparison.found.length > 0 && comparison.missing.length === 0 && (
                  <p className="flex items-center gap-1.5 text-xs text-[#34d399]"><CheckCircle2 size={13} /> Alle Config-Mods sind abgedeckt.</p>
                )}
              </div>
            )}
          </section>
        )}

        {/* Empty state */}
        {results.length === 0 && !checking && (
          <div className="mt-16 flex flex-col items-center text-center text-[var(--muted)]">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl" style={{ background: 'rgba(102,192,244,0.08)' }}>
              <Boxes size={26} className="text-[#66c0f4]" />
            </div>
            <p className="mt-3 text-sm font-medium text-[var(--text)]">Workshop-IDs eingeben</p>
            <p className="mt-1 max-w-xs text-xs">Prüft Zomboid-Mods auf gelöschte, private oder veraltete Items — ohne Steam-Login.</p>
          </div>
        )}
      </div>
    </div>
  )
}
