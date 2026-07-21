import type { CheckResult, CheckStatus } from '../../main/checker'

export type { CheckResult, CheckStatus }

/** Parse a free-form Workshop-ID input (semicolons, commas, whitespace or
 * newlines) into a de-duplicated list of numeric IDs — matches the Python
 * CLI which keeps only `.isdigit()` tokens. */
export function parseWorkshopIds(input: string): string[] {
  const out: string[] = []
  for (const tok of input.split(/[;,\s]+/)) {
    const t = tok.trim()
    if (t && /^\d+$/.test(t) && !out.includes(t)) out.push(t)
  }
  return out
}

/** Parse a free-form Mod-ID input (semicolons/commas/newlines) — Mod IDs are
 * not numeric, so we keep everything non-empty, de-duplicated & in order. */
export function parseModIds(input: string): string[] {
  const out: string[] = []
  for (const tok of input.split(/[;,\n]+/)) {
    const t = tok.trim()
    if (t && !out.includes(t)) out.push(t)
  }
  return out
}

export interface Comparison {
  found: string[]
  missing: string[]
  extra: { workshopId: string; modId: string }[]
}

/** Compare the user's config Mod IDs against everything found on the Workshop
 * pages. Ported from core.py compare_mod_ids. */
export function compareModIds(configIds: string[], results: CheckResult[]): Comparison {
  const workshopMap = new Map<string, string[]>()
  for (const r of results) if (r.modIds && r.modIds.length) workshopMap.set(r.id, r.modIds)

  const workshopValues: string[] = []
  for (const mids of workshopMap.values()) workshopValues.push(...mids)

  const found: string[] = []
  const missing: string[] = []
  for (const cid of configIds) {
    if (workshopValues.includes(cid)) found.push(cid)
    else missing.push(cid)
  }

  const extra: { workshopId: string; modId: string }[] = []
  for (const [wid, mids] of workshopMap) {
    for (const mid of mids) if (!configIds.includes(mid)) extra.push({ workshopId: wid, modId: mid })
  }

  return { found, missing, extra }
}

/** Workshop URL for a given item id. */
export function workshopUrl(id: string): string {
  return `https://steamcommunity.com/sharedfiles/filedetails/?id=${id}`
}
