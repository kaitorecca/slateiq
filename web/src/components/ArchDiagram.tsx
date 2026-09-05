/** Hand-drawn architecture of SlateIQ. Scales to its container; readable on dark. */
export function ArchDiagram() {
  const box = (x: number, y: number, w: number, h: number, fill = '#14171B', stroke = '#252A31') => (
    <rect x={x} y={y} width={w} height={h} rx="9" fill={fill} stroke={stroke} />
  )
  return (
    <svg viewBox="0 0 900 470" className="w-full" role="img" aria-labelledby="arch-title arch-desc">
      <title id="arch-title">SlateIQ architecture</title>
      <desc id="arch-desc">
        Dailies clips and call sheets are analysed by Gemini during ingest and written to ClickHouse. Google ADK
        sub-agents query ClickHouse exclusively through the official mcp-clickhouse server, and serve the React UI via
        FastAPI on Cloud Run.
      </desc>
      <defs>
        <marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
          <path d="M0 0 10 5 0 10z" fill="#4A5058" />
        </marker>
        <marker id="ar-hot" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
          <path d="M0 0 10 5 0 10z" fill="#F0B429" />
        </marker>
        <linearGradient id="hot" x1="0" x2="1">
          <stop offset="0" stopColor="#F0B429" stopOpacity=".15" />
          <stop offset="1" stopColor="#F0B429" stopOpacity=".04" />
        </linearGradient>
      </defs>

      <g fontFamily="ui-sans-serif, system-ui" fontSize="12" fill="#9AA1AB">
        {/* INGEST column */}
        <text x="24" y="30" fontSize="10" letterSpacing="2" fill="#666D77">INGEST (BATCH)</text>
        {box(24, 42, 200, 54)}
        <text x="40" y="64" fill="#E9E7E2" fontSize="12.5" fontWeight="600">Dailies clips · mp4</text>
        <text x="40" y="82" fontSize="11">Tears of Steel → 24 takes</text>

        {box(24, 108, 200, 54)}
        <text x="40" y="130" fill="#E9E7E2" fontSize="12.5" fontWeight="600">Call sheet · script</text>
        <text x="40" y="148" fontSize="11">scenes, pages, characters</text>

        {box(24, 174, 200, 66, 'url(#hot)', '#8A6512')}
        <text x="40" y="198" fill="#F0B429" fontSize="12.5" fontWeight="600">Gemini 3.5 Flash</text>
        <text x="40" y="215" fontSize="11">multimodal video →</text>
        <text x="40" y="230" fontSize="11">structured JSON knowledge</text>

        <path d="M124 96 v10" stroke="#4A5058" markerEnd="url(#ar)" />
        <path d="M124 162 v10" stroke="#4A5058" markerEnd="url(#ar)" />

        {/* ClickHouse */}
        {box(276, 108, 180, 132, '#14171B', '#F0B429')}
        <text x="296" y="134" fill="#F0B429" fontSize="13" fontWeight="700">ClickHouse</text>
        <text x="296" y="154" fontSize="11">take · take_event</text>
        <text x="296" y="171" fontSize="11">scene · shooting_day</text>
        <text x="296" y="188" fontSize="11">continuity_note</text>
        <text x="296" y="205" fontSize="11" fill="#E9E7E2">frame_telemetry</text>
        <text x="296" y="221" fontSize="10" fill="#666D77">millions of rows · e2-micro</text>
        <path d="M224 207 h44" stroke="#4A5058" markerEnd="url(#ar)" />

        {/* MCP */}
        {box(276, 268, 180, 62, 'url(#hot)', '#8A6512')}
        <text x="296" y="292" fill="#F0B429" fontSize="12.5" fontWeight="700">mcp-clickhouse</text>
        <text x="296" y="310" fontSize="10.5">official MCP server · read-only</text>
        <path d="M366 240 v26" stroke="#F0B429" markerEnd="url(#ar-hot)" />
        <path d="M356 266 v-24" stroke="#F0B429" markerEnd="url(#ar-hot)" />

        {/* ADK agents */}
        {box(516, 84, 236, 246)}
        <text x="536" y="110" fill="#E9E7E2" fontSize="13" fontWeight="700">Google ADK agent network</text>
        <text x="536" y="127" fontSize="10.5" fill="#666D77">Gemini · McpToolset</text>
        {box(536, 138, 196, 30, '#1B1F25', '#3A414A')}
        <text x="552" y="157" fill="#F0B429" fontSize="11.5" fontWeight="600">coordinator</text>
        {[
          ['editor_agent', 'take search · circled takes', '#5FBF7F'],
          ['production_agent', 'schedule · DPR · risk', '#5B9FE3'],
          ['continuity_agent', 'cross-take conflicts', '#D9A0F0'],
          ['report_agent', 'markdown → Gemini TTS', '#F09A6A'],
        ].map(([n, d, c], i) => (
          <g key={n} transform={`translate(0 ${176 + i * 38})`}>
            {box(536, 0, 196, 32, '#111417', '#252A31')}
            <circle cx="550" cy="16" r="3.5" fill={c} />
            <text x="562" y="14" fill="#E9E7E2" fontSize="11.5" fontWeight="600">{n}</text>
            <text x="562" y="26" fontSize="9.5" fill="#666D77">{d}</text>
          </g>
        ))}
        <path d="M456 299 h58 v-60" stroke="#F0B429" fill="none" markerEnd="url(#ar-hot)" />
        <text x="462" y="292" fontSize="9.5" fill="#F0B429">run_query</text>

        {/* Serving */}
        <text x="24" y="298" fontSize="10" letterSpacing="2" fill="#666D77">SERVE · CLOUD RUN</text>
        {box(24, 310, 200, 62)}
        <text x="40" y="334" fill="#E9E7E2" fontSize="12.5" fontWeight="600">React UI</text>
        <text x="40" y="352" fontSize="11">chat · takes · dashboards</text>

        {box(24, 386, 200, 58)}
        <text x="40" y="410" fill="#E9E7E2" fontSize="12.5" fontWeight="600">FastAPI</text>
        <text x="40" y="428" fontSize="11">SSE /api/chat · /api/tts</text>
        <path d="M124 386 v-12" stroke="#4A5058" markerEnd="url(#ar)" />
        <path d="M224 428 h552 v-118 h-24" stroke="#4A5058" fill="none" markerEnd="url(#ar)" />

        {box(276, 366, 180, 54)}
        <text x="296" y="389" fill="#E9E7E2" fontSize="12" fontWeight="600">GCS bucket</text>
        <text x="296" y="406" fontSize="10.5">clips + thumbnails</text>

        {box(516, 366, 236, 54)}
        <text x="536" y="389" fill="#E9E7E2" fontSize="12" fontWeight="600">Grafana</text>
        <text x="536" y="406" fontSize="10.5">ClickHouse datasource · embedded</text>
        <path d="M634 366 v-32" stroke="#4A5058" markerEnd="url(#ar)" />

        {/* legend */}
        <g transform="translate(788 84)">
          <rect x="0" y="0" width="88" height="70" rx="8" fill="#111417" stroke="#252A31" />
          <text x="12" y="20" fontSize="9" letterSpacing="1.4" fill="#666D77">RUNTIME</text>
          <line x1="12" y1="34" x2="34" y2="34" stroke="#F0B429" strokeWidth="1.5" />
          <text x="40" y="38" fontSize="9.5" fill="#F0B429">MCP path</text>
          <line x1="12" y1="52" x2="34" y2="52" stroke="#4A5058" strokeWidth="1.5" />
          <text x="40" y="56" fontSize="9.5">plain</text>
        </g>
      </g>
    </svg>
  )
}
