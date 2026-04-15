import { useState, useMemo } from "react";
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { AlertTriangle, TrendingUp, Clock, Shield, Filter, ChevronDown, ChevronUp, ExternalLink, Zap } from "lucide-react";

// ── Sample data (replace with live batch output) ────────────────────

const SAMPLE_RESULTS = [
  {
    document_number: "2026-08001",
    title: "Greenhouse Gas Emissions Standards for Power Plants",
    doc_type: "RULE",
    agency: "Environmental Protection Agency",
    agency_short: "EPA",
    publication_date: "2026-04-10",
    effective_date: "2026-07-01",
    significant: true,
    etfs: ["XLE", "XLU", "XLB", "XOP", "OIH", "TAN", "ICLN", "XME", "LIT", "PHO"],
    industries: [
      { naics: "211", title: "Oil & Gas Extraction" },
      { naics: "221", title: "Utilities" },
      { naics: "324", title: "Petroleum & Coal Products" },
      { naics: "325", title: "Chemical Manufacturing" },
    ],
    contamination_score: 0.33,
    summary: {
      headline: "EPA tightens greenhouse gas emissions standards for power plants",
      brief: "The EPA finalizes a final rule that introduces new performance standards for power plants, utilities, and energy producers.",
      action_verb: "tightens",
      tags: ["emissions", "climate", "power-plants"],
    },
    obligation_type: "RESTRICTS",
  },
  {
    document_number: "2026-08002",
    title: "Climate-Related Financial Risk Disclosures",
    doc_type: "PRORULE",
    agency: "Securities and Exchange Commission",
    agency_short: "SEC",
    publication_date: "2026-04-10",
    effective_date: null,
    significant: true,
    etfs: ["XLF", "KRE", "IAI", "KIE", "XLRE"],
    industries: [
      { naics: "523", title: "Securities & Investments" },
      { naics: "522", title: "Credit Intermediation (Banking)" },
      { naics: "525", title: "Funds, Trusts & Financial Vehicles" },
    ],
    contamination_score: 0.33,
    summary: {
      headline: "SEC requires climate-related financial risk disclosures",
      brief: "The SEC proposes enhanced climate risk disclosure requirements for public companies, broker-dealers, and investment funds.",
      action_verb: "requires",
      tags: ["disclosure", "climate", "financial"],
    },
    obligation_type: "MANDATES",
  },
  {
    document_number: "2026-08003",
    title: "Safety Standards for Autonomous Vehicle Testing",
    doc_type: "RULE",
    agency: "National Highway Traffic Safety Administration",
    agency_short: "NHTSA",
    publication_date: "2026-04-10",
    effective_date: "2026-09-01",
    significant: false,
    etfs: ["JETS", "IYT", "SMH", "XLI"],
    industries: [
      { naics: "336", title: "Transportation Equipment Mfg" },
      { naics: "488", title: "Support for Transportation" },
    ],
    contamination_score: 0.15,
    summary: {
      headline: "NHTSA requires safety standards for autonomous vehicle testing",
      brief: "NHTSA establishes safety framework for autonomous vehicles, affecting automakers and transportation equipment manufacturers.",
      action_verb: "requires",
      tags: ["autonomous-vehicles", "safety", "transportation"],
    },
    obligation_type: "MANDATES",
  },
  {
    document_number: "2026-08004",
    title: "Drug Pricing Transparency Requirements",
    doc_type: "RULE",
    agency: "Department of Health and Human Services",
    agency_short: "HHS",
    publication_date: "2026-04-09",
    effective_date: "2026-06-15",
    significant: true,
    etfs: ["XLV", "XBI", "IBB", "IHI", "IHF"],
    industries: [
      { naics: "325", title: "Chemical Manufacturing (Pharma)" },
      { naics: "621", title: "Ambulatory Health Care" },
      { naics: "622", title: "Hospitals" },
    ],
    contamination_score: 0.45,
    summary: {
      headline: "HHS requires drug pricing transparency requirements",
      brief: "HHS finalizes rules requiring pharmaceutical manufacturers to disclose drug pricing to healthcare providers and insurers.",
      action_verb: "requires",
      tags: ["drug-pricing", "transparency", "healthcare"],
    },
    obligation_type: "MANDATES",
  },
  {
    document_number: "2026-08005",
    title: "Cybersecurity Risk Management for Financial Institutions",
    doc_type: "RULE",
    agency: "Office of the Comptroller of the Currency",
    agency_short: "OCC",
    publication_date: "2026-04-09",
    effective_date: "2026-08-01",
    significant: true,
    etfs: ["XLF", "KRE", "IAI", "HACK", "CIBR"],
    industries: [
      { naics: "522", title: "Credit Intermediation (Banking)" },
      { naics: "523", title: "Securities & Investments" },
    ],
    contamination_score: 0.28,
    summary: {
      headline: "OCC tightens cybersecurity risk management for banks",
      brief: "OCC finalizes cybersecurity risk management requirements for national banks, requiring enhanced security protocols.",
      action_verb: "tightens",
      tags: ["cybersecurity", "banking", "risk-management"],
    },
    obligation_type: "RESTRICTS",
  },
  {
    document_number: "2026-08006",
    title: "Clean Energy Tax Credit Extensions",
    doc_type: "RULE",
    agency: "Internal Revenue Service",
    agency_short: "IRS",
    publication_date: "2026-04-08",
    effective_date: "2026-04-08",
    significant: false,
    etfs: ["TAN", "ICLN", "LIT", "XLU"],
    industries: [
      { naics: "221", title: "Utilities" },
      { naics: "335", title: "Electrical Equipment Mfg" },
    ],
    contamination_score: 0.12,
    summary: {
      headline: "IRS incentivizes clean energy tax credit extensions",
      brief: "IRS extends and expands tax credits for clean energy investments, benefiting solar, wind, and battery manufacturers.",
      action_verb: "incentivizes",
      tags: ["clean-energy", "tax-credits", "incentives"],
    },
    obligation_type: "SUBSIDIZES",
  },
];

// ── Color utilities ─────────────────────────────────────────────────

const OBLIGATION_COLORS = {
  RESTRICTS: { bg: "bg-red-50", border: "border-red-200", text: "text-red-700", badge: "bg-red-100 text-red-800" },
  MANDATES: { bg: "bg-blue-50", border: "border-blue-200", text: "text-blue-700", badge: "bg-blue-100 text-blue-800" },
  SUBSIDIZES: { bg: "bg-green-50", border: "border-green-200", text: "text-green-700", badge: "bg-green-100 text-green-800" },
  EXEMPTS: { bg: "bg-yellow-50", border: "border-yellow-200", text: "text-yellow-700", badge: "bg-yellow-100 text-yellow-800" },
  PERMITS: { bg: "bg-purple-50", border: "border-purple-200", text: "text-purple-700", badge: "bg-purple-100 text-purple-800" },
  MODIFIES_THRESHOLD: { bg: "bg-orange-50", border: "border-orange-200", text: "text-orange-700", badge: "bg-orange-100 text-orange-800" },
};

const DOC_TYPE_LABELS = {
  RULE: "Final Rule",
  PRORULE: "Proposed Rule",
  NOTICE: "Notice",
  PRESDOC: "Presidential",
};

function contaminationColor(score) {
  if (score <= 0.2) return "text-green-600";
  if (score <= 0.4) return "text-yellow-600";
  return "text-red-600";
}

// ── Components ──────────────────────────────────────────────────────

function RegCard({ result, isExpanded, onToggle }) {
  const colors = OBLIGATION_COLORS[result.obligation_type] || OBLIGATION_COLORS.MANDATES;
  const daysUntilEffective = result.effective_date
    ? Math.ceil((new Date(result.effective_date) - new Date()) / (1000 * 60 * 60 * 24))
    : null;

  return (
    <div className={`rounded-lg border-2 ${colors.border} ${colors.bg} p-4 mb-3 transition-all`}>
      <div className="flex items-start justify-between cursor-pointer" onClick={onToggle}>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <span className={`text-xs font-bold px-2 py-0.5 rounded ${colors.badge}`}>
              {result.summary.action_verb.toUpperCase()}
            </span>
            <span className="text-xs font-medium px-2 py-0.5 rounded bg-gray-100 text-gray-700">
              {DOC_TYPE_LABELS[result.doc_type] || result.doc_type}
            </span>
            {result.significant && (
              <span className="text-xs font-bold px-2 py-0.5 rounded bg-amber-100 text-amber-800 flex items-center gap-1">
                <Zap size={10} /> Significant
              </span>
            )}
            <span className={`text-xs font-medium ${contaminationColor(result.contamination_score)}`}>
              Contam: {(result.contamination_score * 100).toFixed(0)}%
            </span>
          </div>
          <h3 className={`font-semibold text-sm ${colors.text} leading-tight`}>
            {result.summary.headline}
          </h3>
          <p className="text-xs text-gray-500 mt-1">
            {result.agency_short} | {result.publication_date} | {result.document_number}
          </p>
        </div>
        <div className="ml-3 flex flex-col items-end shrink-0">
          <div className="text-lg font-bold text-gray-800">{result.etfs.length}</div>
          <div className="text-xs text-gray-500">ETFs</div>
          {isExpanded ? <ChevronUp size={16} className="mt-1 text-gray-400" /> : <ChevronDown size={16} className="mt-1 text-gray-400" />}
        </div>
      </div>

      {isExpanded && (
        <div className="mt-3 pt-3 border-t border-gray-200">
          <p className="text-sm text-gray-700 mb-3">{result.summary.brief}</p>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <div className="text-xs font-semibold text-gray-500 mb-1">Exposed ETFs</div>
              <div className="flex flex-wrap gap-1">
                {result.etfs.map((t) => (
                  <span key={t} className="text-xs px-2 py-0.5 rounded bg-white border border-gray-300 font-mono">
                    {t}
                  </span>
                ))}
              </div>
            </div>
            <div>
              <div className="text-xs font-semibold text-gray-500 mb-1">Industries</div>
              <div className="flex flex-wrap gap-1">
                {result.industries.map((i) => (
                  <span key={i.naics} className="text-xs px-2 py-0.5 rounded bg-white border border-gray-300">
                    {i.title}
                  </span>
                ))}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-4 mt-3 text-xs text-gray-500">
            {result.effective_date && (
              <span className="flex items-center gap-1">
                <Clock size={12} />
                Effective: {result.effective_date}
                {daysUntilEffective !== null && daysUntilEffective > 0 && (
                  <span className="text-orange-600 font-medium">({daysUntilEffective}d)</span>
                )}
              </span>
            )}
            <div className="flex gap-1">
              {result.summary.tags.map((tag) => (
                <span key={tag} className="px-1.5 py-0.5 rounded bg-gray-100 text-gray-600">#{tag}</span>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function ETFHeatmap({ results }) {
  const etfCounts = useMemo(() => {
    const counts = {};
    results.forEach((r) => {
      r.etfs.forEach((t) => {
        counts[t] = (counts[t] || 0) + 1;
      });
    });
    return Object.entries(counts)
      .sort((a, b) => b[1] - a[1])
      .map(([ticker, count]) => ({ ticker, count }));
  }, [results]);

  const maxCount = Math.max(...etfCounts.map((d) => d.count), 1);

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 mb-4">
      <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
        <TrendingUp size={14} /> ETF Exposure Frequency
      </h3>
      <ResponsiveContainer width="100%" height={180}>
        <BarChart data={etfCounts.slice(0, 15)} margin={{ top: 5, right: 5, bottom: 5, left: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis dataKey="ticker" tick={{ fontSize: 10 }} />
          <YAxis tick={{ fontSize: 10 }} allowDecimals={false} />
          <Tooltip
            contentStyle={{ fontSize: 12, borderRadius: 8 }}
            formatter={(val) => [`${val} regulations`, "Mentions"]}
          />
          <Bar dataKey="count" radius={[4, 4, 0, 0]}>
            {etfCounts.slice(0, 15).map((entry, i) => (
              <Cell
                key={entry.ticker}
                fill={`hsl(${210 + (entry.count / maxCount) * 60}, 70%, ${65 - (entry.count / maxCount) * 25}%)`}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

function StatsBar({ results }) {
  const totalETFs = new Set(results.flatMap((r) => r.etfs)).size;
  const significant = results.filter((r) => r.significant).length;
  const avgContam = results.reduce((s, r) => s + r.contamination_score, 0) / (results.length || 1);

  const typeCounts = {};
  results.forEach((r) => {
    typeCounts[r.obligation_type] = (typeCounts[r.obligation_type] || 0) + 1;
  });

  return (
    <div className="grid grid-cols-5 gap-3 mb-4">
      {[
        { label: "Regulations", value: results.length, color: "text-gray-800" },
        { label: "ETFs Exposed", value: totalETFs, color: "text-blue-700" },
        { label: "Significant", value: significant, color: "text-amber-700" },
        { label: "Avg Contamination", value: `${(avgContam * 100).toFixed(0)}%`, color: contaminationColor(avgContam) },
        { label: "Restricts", value: typeCounts.RESTRICTS || 0, color: "text-red-700" },
      ].map((stat) => (
        <div key={stat.label} className="bg-white rounded-lg border border-gray-200 p-3 text-center">
          <div className={`text-xl font-bold ${stat.color}`}>{stat.value}</div>
          <div className="text-xs text-gray-500">{stat.label}</div>
        </div>
      ))}
    </div>
  );
}

function FilterBar({ filters, setFilters, results }) {
  const agencies = [...new Set(results.map((r) => r.agency_short))].sort();
  const obligations = [...new Set(results.map((r) => r.obligation_type))].sort();
  const allETFs = [...new Set(results.flatMap((r) => r.etfs))].sort();

  return (
    <div className="flex gap-2 mb-4 flex-wrap items-center">
      <Filter size={14} className="text-gray-400" />
      <select
        className="text-xs border border-gray-300 rounded px-2 py-1 bg-white"
        value={filters.agency}
        onChange={(e) => setFilters((f) => ({ ...f, agency: e.target.value }))}
      >
        <option value="">All Agencies</option>
        {agencies.map((a) => <option key={a} value={a}>{a}</option>)}
      </select>
      <select
        className="text-xs border border-gray-300 rounded px-2 py-1 bg-white"
        value={filters.obligation}
        onChange={(e) => setFilters((f) => ({ ...f, obligation: e.target.value }))}
      >
        <option value="">All Types</option>
        {obligations.map((o) => <option key={o} value={o}>{o}</option>)}
      </select>
      <select
        className="text-xs border border-gray-300 rounded px-2 py-1 bg-white"
        value={filters.etf}
        onChange={(e) => setFilters((f) => ({ ...f, etf: e.target.value }))}
      >
        <option value="">All ETFs</option>
        {allETFs.map((t) => <option key={t} value={t}>{t}</option>)}
      </select>
      <label className="flex items-center gap-1 text-xs text-gray-600">
        <input
          type="checkbox"
          checked={filters.significantOnly}
          onChange={(e) => setFilters((f) => ({ ...f, significantOnly: e.target.checked }))}
          className="rounded"
        />
        Significant only
      </label>
      {(filters.agency || filters.obligation || filters.etf || filters.significantOnly) && (
        <button
          className="text-xs text-blue-600 underline"
          onClick={() => setFilters({ agency: "", obligation: "", etf: "", significantOnly: false })}
        >
          Clear
        </button>
      )}
    </div>
  );
}

// ── Main App ────────────────────────────────────────────────────────

export default function LegalizeFeed() {
  const [expandedId, setExpandedId] = useState(null);
  const [filters, setFilters] = useState({
    agency: "",
    obligation: "",
    etf: "",
    significantOnly: false,
  });

  const filtered = useMemo(() => {
    return SAMPLE_RESULTS.filter((r) => {
      if (filters.agency && r.agency_short !== filters.agency) return false;
      if (filters.obligation && r.obligation_type !== filters.obligation) return false;
      if (filters.etf && !r.etfs.includes(filters.etf)) return false;
      if (filters.significantOnly && !r.significant) return false;
      return true;
    });
  }, [filters]);

  return (
    <div className="max-w-3xl mx-auto p-4 bg-gray-50 min-h-screen">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Shield size={24} className="text-blue-600" />
          Legalize
        </h1>
        <p className="text-sm text-gray-500 mt-1">
          Regulation-to-Exposure Mapping Feed
        </p>
      </div>

      <StatsBar results={filtered} />
      <ETFHeatmap results={filtered} />
      <FilterBar filters={filters} setFilters={setFilters} results={SAMPLE_RESULTS} />

      <div className="space-y-0">
        {filtered.length === 0 ? (
          <div className="text-center py-12 text-gray-400">
            <AlertTriangle size={32} className="mx-auto mb-2" />
            <p>No regulations match your filters</p>
          </div>
        ) : (
          filtered.map((r) => (
            <RegCard
              key={r.document_number}
              result={r}
              isExpanded={expandedId === r.document_number}
              onToggle={() => setExpandedId(expandedId === r.document_number ? null : r.document_number)}
            />
          ))
        )}
      </div>

      <div className="mt-6 text-center text-xs text-gray-400">
        Legalize v0.1 | {filtered.length} of {SAMPLE_RESULTS.length} regulations shown
        <br />
        Data: Federal Register API | Holdings: iShares | Contamination: Macro Calendar
      </div>
    </div>
  );
}
