const KEYWORDS =
  'SELECT|FROM|WHERE|GROUP\\s+BY|ORDER\\s+BY|LIMIT|OFFSET|JOIN|LEFT|RIGHT|INNER|OUTER|FULL|ON|AS|AND|OR|NOT|IN|IS|NULL|LIKE|ILIKE|BETWEEN|CASE|WHEN|THEN|ELSE|END|WITH|UNION|ALL|DISTINCT|HAVING|ASC|DESC|ARRAY\\s+JOIN|PREWHERE|SETTINGS|FINAL|SAMPLE|FORMAT|INTERVAL|USING|EXISTS'
const FUNCS =
  'count|sum|avg|min|max|round|toDate|toDateTime|toStartOfDay|toStartOfHour|arrayJoin|groupArray|any|anyLast|uniq|uniqExact|quantile|quantiles|argMax|argMin|has|length|lower|upper|concat|coalesce|if|multiIf|ifNull|nullIf|abs|now|today|dateDiff|formatDateTime|splitByChar|toString|toFloat64|toInt32|toUInt32|countIf|sumIf|avgIf|topK'

export interface SqlToken {
  text: string
  cls: string
}

const RE = new RegExp(
  [
    `(--[^\\n]*|/\\*[\\s\\S]*?\\*/)`, // 1 comment
    `('(?:''|\\\\.|[^'])*')`, // 2 string
    `\\b(${KEYWORDS})\\b`, // 3 keyword
    `\\b(${FUNCS})\\s*(?=\\()`, // 4 function
    `\\b(\\d+(?:\\.\\d+)?)\\b`, // 5 number
    `([=<>!+\\-*/%,;()\\[\\].]+)`, // 6 operator
  ].join('|'),
  'gi',
)

/** Tiny dependency-free SQL tokenizer for display. */
export function tokenizeSql(sql: string): SqlToken[] {
  const out: SqlToken[] = []
  let last = 0
  for (const m of sql.matchAll(RE)) {
    const i = m.index ?? 0
    if (i > last) out.push({ text: sql.slice(last, i), cls: '' })
    const cls = m[1] ? 'sql-com' : m[2] ? 'sql-str' : m[3] ? 'sql-kw' : m[4] ? 'sql-fn' : m[5] ? 'sql-num' : 'sql-op'
    out.push({ text: m[0], cls })
    last = i + m[0].length
  }
  if (last < sql.length) out.push({ text: sql.slice(last), cls: '' })
  return out
}

/** Light pretty-print so one-line agent SQL reads well in the trace panel. */
export function formatSql(sql: string): string {
  const s = sql.replace(/\s+/g, ' ').trim()
  return s
    .replace(
      /\s+(FROM|WHERE|GROUP BY|ORDER BY|LIMIT|HAVING|LEFT JOIN|INNER JOIN|RIGHT JOIN|JOIN|UNION ALL|UNION|SETTINGS|PREWHERE|ARRAY JOIN)\b/gi,
      '\n$1',
    )
    .replace(/\s+(AND|OR)\b/gi, '\n  $1')
}
