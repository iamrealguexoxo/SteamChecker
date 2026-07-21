/* Steam Workshop item checker — faithful TypeScript port of the Python
 * reference implementation (python/steam_checker/core.py in the original
 * SteamChecker repo). Runs in Electron's main process so the HTTP request to
 * steamcommunity.com has no CORS restriction (the whole reason a desktop
 * shell beats a browser tool here). Title/Mod-ID extraction regexes and the
 * warning rules are kept byte-for-byte equivalent to the original. */

export type CheckStatus = 'OK' | 'GELÖSCHT' | 'NO_TITLE' | 'FEHLER' | 'TIMEOUT'

export interface CheckResult {
  id: string
  status: CheckStatus
  /** cleaned page title (without the appended [ID: …] suffix) */
  title: string | null
  warning: string | null
  error: string | null
  modIds: string[] | null
}

const USER_AGENT =
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

/** Minimal HTML-entity decode — mirrors Python's html.unescape for the
 * entities Steam actually emits (&amp; in mod IDs, quotes, nbsp, numeric). */
function unescapeHtml(input: string): string {
  return input
    .replace(/&amp;/gi, '&')
    .replace(/&lt;/gi, '<')
    .replace(/&gt;/gi, '>')
    .replace(/&quot;/gi, '"')
    .replace(/&#0*39;|&apos;/gi, "'")
    .replace(/&nbsp;/gi, ' ')
    .replace(/&#(\d+);/g, (_, n) => String.fromCodePoint(Number(n)))
    .replace(/&#x([0-9a-f]+);/gi, (_, n) => String.fromCodePoint(parseInt(n, 16)))
}

function extractTitle(html: string): string | null {
  // Primary: div.workshopItemTitle
  let m = html.match(/<div\s+class="workshopItemTitle">([\s\S]*?)<\/div>/i)
  if (m && m[1].trim()) return m[1].trim()

  // Fallback: og:title
  m = html.match(/<meta\s+property="og:title"\s+content="([\s\S]*?)"/i)
  if (m && m[1].trim()) return m[1].trim()

  return null
}

const NOISE_WORDS = new Set([
  'is', 'are', 'from', 'here', 'some', 'mods', 'mod', 'and', 'the', 'not',
  'all', 'for', 'you', 'too', 'can', 'have', 'your', 'my', 'own', 'unique',
  'idea', 'developed', 'just', 'time', 'created', 'paid', 'hidden', 'private',
  'use', 'please', 'this', 'that', 'they', 'these', 'those',
])

function looksLikeNoise(token: string): boolean {
  const lower = token.toLowerCase()
  if (NOISE_WORDS.has(lower)) return true
  if (token.length <= 3 && /^[a-z]+$/.test(token)) return true
  return false
}

/** Extract one or more Mod IDs. Ported from core.py _extract_mod_ids:
 * 1) quoted IDs win, 2) unquoted candidates are trimmed to ID-like tokens,
 * short multi-word IDs (e.g. "More Gloves") are allowed while sentences are
 * rejected, 3) separators ; , / split multiple IDs on one line, 4) unique &
 * order-preserving. */
function extractModIds(html: string): string[] | null {
  const results: string[] = []

  const quotedPat =
    /(?:<b>\s*Mod\s*ID:\s*<\/b>\s*=\s*|Mod\s*ID\s*:?\s*)("([^"]+)"|'([^']+)')/gis
  const unquotedPat =
    /(?:<b>\s*Mod\s*ID:\s*<\/b>\s*=\s*|Mod\s*ID\s*:?\s*)([A-Za-z0-9_\-.[\]()&][^<\r\n]*)/gi

  // 1) Quoted IDs
  for (const m of html.matchAll(quotedPat)) {
    const val = (m[2] || m[3] || '').trim()
    if (val && !results.includes(val)) results.push(val)
  }

  // 2) Unquoted candidates
  const stoppers = ['Workshop ID:', 'Map Folder:', 'Version:', 'Mod ID:']
  for (const m of html.matchAll(unquotedPat)) {
    let candidate = m[1].trim()
    if (!candidate) continue
    candidate = unescapeHtml(candidate)

    for (const stopper of stoppers) {
      const pos = candidate.indexOf(stopper)
      if (pos > 0) candidate = candidate.slice(0, pos).trim()
    }

    const normalized = candidate.replace(/\s+/g, ' ').trim()
    const words = normalized.split(' ')

    // short multi-word IDs, avoiding descriptive sentences
    if (words.length > 1 && words.length <= 4) {
      const multi = /^[A-Za-z0-9_\-.[\]()&]+(?:\s+[A-Za-z0-9_\-.[\]()&]+){1,3}$/.test(normalized)
      if (multi) {
        const wordOk = (w: string) => {
          const first = w[0]
          return first >= 'A' && first <= 'Z' || /[0-9]/.test(first) || '[(&'.includes(first)
        }
        if (words.every(wordOk)) {
          if (!results.includes(normalized)) results.push(normalized)
          continue
        }
      }
    }

    if (normalized.includes(' ') && !/[;,/]/.test(normalized)) {
      // spaces but not a qualified multi-word ID and no separators → prose
      continue
    }

    const seg = candidate.match(/[A-Za-z0-9_\-.[\]()&]+(?:[;,/]\s*[A-Za-z0-9_\-.[\]()&]+)*/)
    if (!seg) continue
    const tokens = seg[0].split(/[;,/]+\s*/)
    for (const raw of tokens) {
      const t = raw.trim()
      if (!t) continue
      if (looksLikeNoise(t)) break // narrative text begins — stop this line
      if (!results.includes(t)) results.push(t)
    }
  }

  return results.length ? results : null
}

/** Fetch + evaluate a single Workshop item. */
export async function checkWorkshopItem(
  workshopId: string,
  timeoutMs = 12000
): Promise<CheckResult> {
  const url = `https://steamcommunity.com/sharedfiles/filedetails/?id=${workshopId}`
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)

  try {
    const res = await fetch(url, {
      headers: { 'User-Agent': USER_AGENT },
      signal: controller.signal,
      redirect: 'follow',
    })

    if (res.status === 404) {
      return { id: workshopId, status: 'GELÖSCHT', title: null, warning: null, error: null, modIds: null }
    }

    const html = await res.text()

    if (html.includes('This item has been deleted') || html.includes('removed from the workshop')) {
      return { id: workshopId, status: 'GELÖSCHT', title: null, warning: null, error: null, modIds: null }
    }

    const rawTitle = extractTitle(html)
    if (!rawTitle) {
      return { id: workshopId, status: 'NO_TITLE', title: null, warning: null, error: null, modIds: null }
    }

    const title = unescapeHtml(rawTitle.trim())
    const lowTitle = title.toLowerCase()
    // Generic/error titles Steam serves for removed, private or non-existent
    // items (they return HTTP 200, so the title is the only tell). The Python
    // reference only caught the first of these — an invalid ID slipped through
    // as "OK"; catching the error page too closes that gap.
    if (
      lowTitle.includes('project zomboid :: steam community') ||
      lowTitle === 'steam community :: error' ||
      lowTitle === 'steam community'
    ) {
      return { id: workshopId, status: 'GELÖSCHT', title: null, warning: null, error: null, modIds: null }
    }

    let modIds = extractModIds(html)
    if (modIds) {
      const cleaned: string[] = []
      for (const m of modIds) {
        const mm = unescapeHtml(m).trim()
        if (mm && !cleaned.includes(mm)) cleaned.push(mm)
      }
      modIds = cleaned.length ? cleaned : null
    }

    let warning: string | null = null
    const low = title.toLowerCase()
    if (low.includes('outdated') || low.includes('working outdated')) warning = '[ACHTUNG OUTDATE]'
    if (title.includes('B42') && !title.includes('B41')) warning = '[ANDERE VERSION]'

    return { id: workshopId, status: 'OK', title, warning, error: null, modIds }
  } catch (e: unknown) {
    if (e instanceof Error && e.name === 'AbortError') {
      return { id: workshopId, status: 'TIMEOUT', title: null, warning: null, error: 'Anfrage hat zu lange gedauert', modIds: null }
    }
    return { id: workshopId, status: 'FEHLER', title: null, warning: null, error: e instanceof Error ? e.message : String(e), modIds: null }
  } finally {
    clearTimeout(timer)
  }
}
