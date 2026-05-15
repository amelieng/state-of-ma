import { useEffect, useRef, useState } from 'react'

const YEARS  = [1997,1998,1999,2000,2001,2002,2003,2004,2006,2007,2012,2013,2014,2015,2016,2017,2018,2019,2020,2021,2022,2023,2024]
const SUPPLY = [249,757,1147,567,883,772,1508,1079,2419,1041,1776,2561,2841,4955,3348,5085,3602,2993,3532,3512,3935,2051,1789]
const DEMAND = YEARS.map(y => y <= 2001 ? 3000 : y <= 2007 ? 4000 : y <= 2014 ? 4500 : 5000)

const TABLE_ROWS = [
  {
    era: 'Late 1990s',
    sub: '1997–2001 · 5 yrs',
    built: '3,603',
    need: '~15,000',
    gap: '−11,397',
    note: 'Recovery-era demand surged; building barely moved',
  },
  {
    era: '2000s build & crash',
    sub: '2002–2007 · 5 yrs w/ data',
    built: '7,819',
    need: '~20,000',
    gap: '−12,181',
    note: 'Pre-GFC peak (2006) still fell short; crash wiped gains',
  },
  {
    era: 'Walsh-era boom',
    sub: '2012–2019 · 8 yrs',
    built: '27,873',
    need: '~36,000',
    gap: '−8,127',
    note: 'Best sustained effort in decades — still not enough',
  },
  {
    era: 'COVID & rate shock',
    sub: '2020–2024 · 5 yrs',
    built: '14,879',
    need: '~25,000',
    gap: '−10,121',
    note: 'Rates killed financing; 2024 near decade low',
  },
]

const STAT_CARDS = [
  { val: '~95,000',  color: 'var(--gap-color)',     label: 'Estimated units short since 1997' },
  { val: '19 of 23', color: 'var(--gap-color)',     label: 'Years supply fell short of true need' },
  { val: '0',        color: 'var(--surplus-color)', label: 'Years supply fully met the housing shortage buildup' },
]

const TH_STYLE = {
  fontFamily: 'var(--font-data)',
  fontSize: '11px',
  letterSpacing: '0.08em',
  textTransform: 'uppercase',
  color: 'var(--text-muted)',
  fontWeight: 500,
  textAlign: 'left',
  padding: '6px 16px 10px 0',
  borderBottom: '1px solid var(--border)',
  whiteSpace: 'nowrap',
}

const MOBILE_MQ = '(max-width: 600px), (hover: none) and (pointer: coarse)'

// ── Shared chart config builder ─────────────────────────────────────────────
function buildChartConfig(isMobile) {
  return {
    type: 'line',
    data: {
      labels: YEARS,
      datasets: [
        {
          label: 'Homes permitted',
          data: SUPPLY,
          borderColor: '#3B6B8A',
          borderWidth: 2,
          pointRadius: isMobile ? 2.5 : 3,
          pointHoverRadius: isMobile ? 6 : 5,
          pointHitRadius: isMobile ? 18 : 8,
          pointBackgroundColor: '#3B6B8A',
          pointBorderColor: '#3B6B8A',
          tension: 0.3,
          fill: {
            target: 1,
            above: 'rgba(59,107,138,0.08)',
            below: 'rgba(184,64,64,0.10)',
          },
          order: 1,
        },
        {
          label: 'True need (new households + shortage buildup)',
          data: DEMAND,
          borderColor: '#C17D3C',
          borderWidth: 2,
          borderDash: [5, 3],
          pointRadius: 0,
          pointHitRadius: 0,
          tension: 0,
          fill: false,
          order: 2,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      layout: {
        padding: { right: isMobile ? 6 : 0, top: 4 },
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          enabled: true,
          position: 'nearest',
          backgroundColor: 'rgba(28,25,22,0.94)',
          titleFont: { family: 'Lato', size: 12, weight: '700' },
          bodyFont:  { family: 'Lato', size: 12 },
          footerFont:{ family: 'Lato', size: 12 },
          footerColor: 'rgba(255,255,255,0.75)',
          padding: { top: 8, bottom: 8, left: 10, right: 10 },
          caretPadding: 6,
          boxPadding: 4,
          callbacks: {
            title: ctx => String(ctx[0].label),
            label: ctx => {
              const label = ctx.datasetIndex === 0 ? 'Permitted' : 'True need'
              return `  ${label}: ${Number(ctx.parsed.y).toLocaleString()}`
            },
            footer: ctx => {
              const idx = ctx[0].dataIndex
              const diff = SUPPLY[idx] - DEMAND[idx]
              return diff < 0
                ? `  Shortfall: ${Math.abs(diff).toLocaleString()}`
                : `  Surplus: ${diff.toLocaleString()}`
            },
          },
        },
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: {
            font: { family: 'Lato', size: isMobile ? 10 : 11, weight: '400' },
            color: '#6B6560',
            maxRotation: isMobile ? 0 : 45,
            minRotation: 0,
            autoSkip: true,
            autoSkipPadding: isMobile ? 14 : 8,
            maxTicksLimit: isMobile ? 6 : undefined,
          },
        },
        y: {
          min: 0,
          max: 6500,
          title: {
            display: !isMobile,
            text: 'UNITS / YEAR',
            font: { family: 'Lato', size: 10, weight: '400' },
            color: '#A09C97',
          },
          ticks: {
            font: { family: 'Lato', size: isMobile ? 10 : 11, weight: '400' },
            color: '#6B6560',
            callback: val => val.toLocaleString(),
            maxTicksLimit: isMobile ? 5 : 8,
          },
          grid: { color: 'rgba(226,221,214,0.7)' },
        },
      },
    },
  }
}

export default function SupplyGapChart() {
  const chartRef = useRef(null)
  const [isMobile, setIsMobile] = useState(() =>
    typeof window !== 'undefined' && window.matchMedia(MOBILE_MQ).matches
  )
  const [tableOpen, setTableOpen] = useState(false)

  useEffect(() => {
    if (typeof window === 'undefined') return
    const mq = window.matchMedia(MOBILE_MQ)
    const handler = e => setIsMobile(e.matches)
    mq.addEventListener('change', handler)
    return () => mq.removeEventListener('change', handler)
  }, [])

  // Chart init — re-runs when switching between mobile/desktop so axis
  // ticks/tooltip dimensions are tuned for the current layout.
  useEffect(() => {
    const initChart = () => {
      const Chart = window.Chart
      if (!Chart) return
      const canvas = document.getElementById('supplyGapChart')
      if (!canvas) return
      const existing = Chart.getChart(canvas)
      if (existing) existing.destroy()
      const chart = new Chart(canvas, buildChartConfig(isMobile))
      chartRef.current = chart
      requestAnimationFrame(() => chart.resize())
      setTimeout(() => chart.resize(), 100)
    }

    if (window.Chart) {
      initChart()
    } else {
      let script = document.getElementById('chartjs-cdn')
      if (!script) {
        script = document.createElement('script')
        script.id = 'chartjs-cdn'
        script.src = 'https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js'
        document.head.appendChild(script)
      }
      script.addEventListener('load', initChart)
    }

    return () => {
      if (chartRef.current) {
        chartRef.current.destroy()
        chartRef.current = null
      }
    }
  }, [isMobile])

  // ── Mobile render ─────────────────────────────────────────────────────────
  if (isMobile) {
    return (
      <section className="sg-wrap" style={{ maxWidth: '1160px', margin: '0 auto', padding: '56px 48px 56px' }}>

        {/* Eyebrow */}
        <p style={{
          fontFamily: 'var(--font-data)',
          fontSize: '13px',
          letterSpacing: '0.12em',
          textTransform: 'uppercase',
          color: 'var(--text-muted)',
          marginBottom: '14px',
        }}>
          Supply vs. need · 1997–2024
        </p>

        {/* Heading */}
        <h2 className="sg-heading" style={{
          fontFamily: 'var(--font-heading)',
          fontSize: '28px',
          fontWeight: 700,
          letterSpacing: '-0.3px',
          lineHeight: 1.2,
          color: 'var(--text-primary)',
          marginBottom: '10px',
        }}>
          Even in Boston's best building years, we never dug out of the hole
        </h2>

        {/* Takeaway / subhead */}
        <p className="sg-subhead" style={{
          fontFamily: 'var(--font-body)',
          fontSize: '16px',
          lineHeight: 1.7,
          color: 'var(--text-primary)',
          marginBottom: '24px',
        }}>
          It's not just about new households forming — it's about the housing shortage buildup from years of falling
          short. As that shortage kept growing decade over decade, even a building boom in 2013–2019 wasn't enough
          to close the gap. That's why prices never came down.
        </p>

        {/* Stat cards — 3-up horizontal */}
        <div className="sg-stats" style={{ display: 'flex', gap: '16px', marginBottom: '20px', flexWrap: 'wrap' }}>
          {STAT_CARDS.map(({ val, color, label }) => (
            <div key={label} style={{
              flex: '1 1 200px',
              background: 'var(--surface)',
              border: '1px solid var(--border)',
              borderRadius: '8px',
              padding: '20px',
            }}>
              <div style={{
                fontFamily: 'var(--font-heading)',
                fontSize: 'var(--size-callout)',
                fontWeight: 700,
                color,
                lineHeight: 1,
                marginBottom: '8px',
              }}>
                {val}
              </div>
              <div style={{
                fontFamily: 'var(--font-data)',
                fontSize: '13px',
                color: 'var(--text-secondary)',
                lineHeight: 1.4,
              }}>
                {label}
              </div>
            </div>
          ))}
        </div>

        {/* ── Chart card ── */}
        <div className="sg-chart-card" style={{
          background: 'var(--surface)',
          border: '1px solid var(--border)',
          borderRadius: '12px',
          padding: '18px 12px 12px',
          marginBottom: '24px',
          boxShadow: '0 1px 2px rgba(28,25,22,0.04)',
        }}>

          {/* Pill legend */}
          <div style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: '6px',
            marginBottom: '14px',
            paddingLeft: '4px',
          }}>
            <LegendPill>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                <svg width="18" height="10" style={{ flexShrink: 0 }} aria-hidden="true">
                  <line x1="0" y1="5" x2="18" y2="5" stroke="#3B6B8A" strokeWidth="2" />
                  <circle cx="9" cy="5" r="2.5" fill="#3B6B8A" />
                </svg>
              </span>
              Homes permitted
            </LegendPill>
            <LegendPill>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                <svg width="18" height="10" style={{ flexShrink: 0 }} aria-hidden="true">
                  <line x1="0" y1="5" x2="18" y2="5" stroke="#C17D3C" strokeWidth="2" strokeDasharray="4,2" />
                </svg>
              </span>
              True need
            </LegendPill>
            <LegendPill>
              <span style={{
                display: 'inline-block',
                width: '12px',
                height: '8px',
                background: 'rgba(184,64,64,0.28)',
                borderRadius: '2px',
                flexShrink: 0,
              }} aria-hidden="true" />
              Shortfall
            </LegendPill>
          </div>

          {/* Canvas */}
          <div style={{ height: '280px', position: 'relative', width: '100%' }}>
            <canvas id="supplyGapChart" />
          </div>

          {/* Hint */}
          <p style={{
            fontFamily: 'var(--font-data)',
            fontSize: '11px',
            color: 'var(--text-muted)',
            margin: '10px 0 2px',
            textAlign: 'center',
            fontStyle: 'italic',
          }}>
            Tap or drag across the chart to see year-by-year detail
          </p>
        </div>

        {/* ── Era summary cards ── */}
        <p style={{
          fontFamily: 'var(--font-heading)',
          fontSize: '17px',
          fontWeight: 700,
          color: 'var(--text-primary)',
          lineHeight: 1.35,
          marginBottom: '14px',
        }}>
          The housing shortage buildup grew in every era — even when building picked up
        </p>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '16px' }}>
          {TABLE_ROWS.map(row => <EraCard key={row.era} row={row} />)}
        </div>

        {/* View full table button */}
        <button
          onClick={() => setTableOpen(true)}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
            width: '100%',
            background: 'var(--surface)',
            border: '1px solid var(--border)',
            borderRadius: '10px',
            padding: '14px 16px',
            fontFamily: 'var(--font-data)',
            fontSize: '14px',
            fontWeight: 500,
            letterSpacing: '0.04em',
            color: 'var(--text-secondary)',
            cursor: 'pointer',
            marginBottom: '16px',
          }}
        >
          View full comparison table
          <span style={{ fontSize: '14px', color: 'var(--text-muted)' }}>↗</span>
        </button>

        {/* Sources */}
        <p className="ftb-source" style={{ marginTop: '4px' }}>
          Sources: MA DHCD Building Permit Survey, Boston proper, 1997–2024 · U.S. Census Bureau, ACS Table B11001 (Household Type), annual 1-year estimates · EOHLC Housing Needs Assessment · Metro Mayors Coalition. See methodology for demand line construction.
        </p>

        {/* Bottom sheet — full comparison table */}
        {tableOpen && (
          <>
            <div
              onClick={() => setTableOpen(false)}
              style={{
                position: 'fixed', inset: 0,
                background: 'rgba(28,25,22,0.45)',
                zIndex: 1000,
              }}
            />
            <div
              role="dialog"
              aria-label="Full comparison table"
              style={{
                position: 'fixed',
                left: 0, right: 0, bottom: 0,
                background: 'var(--surface)',
                borderTopLeftRadius: '16px',
                borderTopRightRadius: '16px',
                padding: '10px 0 20px',
                zIndex: 1001,
                maxHeight: '85vh',
                display: 'flex',
                flexDirection: 'column',
                boxShadow: '0 -8px 32px rgba(28,25,22,0.18)',
              }}
            >
              {/* Drag handle */}
              <div style={{
                width: '36px',
                height: '4px',
                borderRadius: '2px',
                background: 'var(--border)',
                margin: '4px auto 14px',
                flexShrink: 0,
              }} />

              {/* Header */}
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '0 20px 12px',
                borderBottom: '1px solid var(--border)',
                flexShrink: 0,
              }}>
                <p style={{
                  fontFamily: 'var(--font-heading)',
                  fontSize: '15px',
                  fontWeight: 700,
                  color: 'var(--text-primary)',
                  margin: 0,
                  lineHeight: 1.3,
                  paddingRight: '12px',
                }}>
                  The housing shortage buildup grew in every era — even when building picked up
                </p>
                <button
                  onClick={() => setTableOpen(false)}
                  aria-label="Close"
                  style={{
                    flexShrink: 0,
                    background: 'transparent',
                    border: 'none',
                    fontSize: '20px',
                    color: 'var(--text-muted)',
                    cursor: 'pointer',
                    lineHeight: 1,
                    padding: '4px 8px',
                  }}
                >×</button>
              </div>

              {/* Scrollable table area */}
              <div style={{
                overflowY: 'auto',
                overflowX: 'auto',
                WebkitOverflowScrolling: 'touch',
                padding: '12px 20px 20px',
                flex: 1,
                minHeight: 0,
              }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: '540px' }}>
                  <thead>
                    <tr>
                      <th style={TH_STYLE}>Era</th>
                      <th style={TH_STYLE}>Homes built</th>
                      <th style={TH_STYLE}>True need</th>
                      <th style={TH_STYLE}>Net gap</th>
                      <th style={{ ...TH_STYLE, whiteSpace: 'normal' }}>What it meant</th>
                    </tr>
                  </thead>
                  <tbody>
                    {TABLE_ROWS.map((row, i) => (
                      <tr key={i} style={{ borderBottom: i < TABLE_ROWS.length - 1 ? '1px solid var(--border)' : 'none' }}>
                        <td style={{ padding: '12px 16px 12px 0', verticalAlign: 'top', minWidth: '140px' }}>
                          <div style={{
                            fontFamily: 'var(--font-heading)',
                            fontSize: '14px',
                            fontWeight: 700,
                            color: 'var(--text-primary)',
                            lineHeight: 1.2,
                          }}>
                            {row.era}
                          </div>
                          <div style={{
                            fontFamily: 'var(--font-data)',
                            fontSize: '10px',
                            color: '#A09C97',
                            marginTop: '3px',
                          }}>
                            {row.sub}
                          </div>
                        </td>
                        <td style={{
                          padding: '12px 16px 12px 0',
                          fontFamily: 'var(--font-data)',
                          fontSize: '13px',
                          color: 'var(--text-primary)',
                          verticalAlign: 'top',
                          whiteSpace: 'nowrap',
                        }}>
                          {row.built}
                        </td>
                        <td style={{
                          padding: '12px 16px 12px 0',
                          fontFamily: 'var(--font-data)',
                          fontSize: '13px',
                          color: 'var(--text-primary)',
                          verticalAlign: 'top',
                          whiteSpace: 'nowrap',
                        }}>
                          {row.need}
                        </td>
                        <td style={{ padding: '12px 16px 12px 0', verticalAlign: 'top', whiteSpace: 'nowrap' }}>
                          <span style={{
                            display: 'inline-block',
                            background: 'rgba(184,64,64,0.10)',
                            color: '#8B2E2E',
                            borderRadius: '2px',
                            fontFamily: 'var(--font-data)',
                            fontSize: '11px',
                            padding: '2px 6px',
                          }}>
                            {row.gap}
                          </span>
                        </td>
                        <td style={{
                          padding: '12px 0 12px 0',
                          fontFamily: 'var(--font-body)',
                          fontSize: '12px',
                          color: '#6B6560',
                          verticalAlign: 'top',
                          lineHeight: 1.55,
                        }}>
                          {row.note}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}

      </section>
    )
  }

  // ── Desktop render (unchanged from prior version) ─────────────────────────
  return (
    <section className="sg-wrap" style={{ maxWidth: '1160px', margin: '0 auto', padding: '56px 48px 56px' }}>

      {/* ── Eyebrow ── */}
      <p style={{
        fontFamily: 'var(--font-data)',
        fontSize: '13px',
        letterSpacing: '0.12em',
        textTransform: 'uppercase',
        color: 'var(--text-muted)',
        marginBottom: '14px',
      }}>
        Supply vs. need · 1997–2024
      </p>

      {/* ── Heading ── */}
      <h2 className="sg-heading" style={{
        fontFamily: 'var(--font-heading)',
        fontSize: '28px',
        fontWeight: 700,
        letterSpacing: '-0.3px',
        lineHeight: 1.2,
        color: 'var(--text-primary)',
        marginBottom: '10px',
      }}>
        Even in Boston's best building years, we never dug out of the hole
      </h2>

      {/* ── Subhead ── */}
      <p className="sg-subhead" style={{
        fontFamily: 'var(--font-body)',
        fontSize: '16px',
        lineHeight: 1.7,
        color: 'var(--text-primary)',
        marginBottom: '32px',
      }}>
        It's not just about new households forming — it's about the housing shortage buildup from years of falling
        short. As that shortage kept growing decade over decade, even a building boom in 2013–2019 wasn't enough
        to close the gap. That's why prices never came down.
      </p>

      {/* ── Stat cards ── */}
      <div className="sg-stats" style={{ display: 'flex', gap: '16px', marginBottom: '24px', flexWrap: 'wrap' }}>
        {STAT_CARDS.map(({ val, color, label }) => (
          <div key={label} style={{
            flex: '1 1 200px',
            background: 'var(--surface)',
            border: '1px solid var(--border)',
            borderRadius: '8px',
            padding: '20px',
          }}>
            <div style={{
              fontFamily: 'var(--font-heading)',
              fontSize: 'var(--size-callout)',
              fontWeight: 700,
              color,
              lineHeight: 1,
              marginBottom: '8px',
            }}>
              {val}
            </div>
            <div style={{
              fontFamily: 'var(--font-data)',
              fontSize: '13px',
              color: 'var(--text-secondary)',
              lineHeight: 1.4,
            }}>
              {label}
            </div>
          </div>
        ))}
      </div>

      {/* ── Chart card ── */}
      <div className="sg-chart-card" style={{
        background: 'var(--surface)',
        border: '1px solid var(--border)',
        borderRadius: '10px',
        padding: '28px 16px 16px',
        marginBottom: '16px',
      }}>

        {/* Custom legend */}
        <div style={{ display: 'flex', gap: '24px', marginBottom: '20px', flexWrap: 'wrap', paddingLeft: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '7px' }}>
            <svg width="22" height="14" style={{ flexShrink: 0 }}>
              <line x1="0" y1="7" x2="22" y2="7" stroke="#3B6B8A" strokeWidth="2" />
              <circle cx="11" cy="7" r="3.5" fill="#3B6B8A" />
            </svg>
            <span style={{ fontFamily: 'var(--font-data)', fontSize: '13px', color: 'var(--text-secondary)' }}>
              Homes permitted
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '7px' }}>
            <svg width="22" height="14" style={{ flexShrink: 0 }}>
              <line x1="0" y1="7" x2="22" y2="7" stroke="#C17D3C" strokeWidth="2" strokeDasharray="5,3" />
            </svg>
            <span style={{ fontFamily: 'var(--font-data)', fontSize: '13px', color: 'var(--text-secondary)' }}>
              True need (new households + shortage buildup)
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '7px' }}>
            <div style={{
              width: '16px',
              height: '10px',
              background: 'rgba(184,64,64,0.28)',
              flexShrink: 0,
              borderRadius: '1px',
            }} />
            <span style={{ fontFamily: 'var(--font-data)', fontSize: '13px', color: 'var(--text-secondary)' }}>
              Shortfall
            </span>
          </div>
        </div>

        {/* Canvas */}
        <div style={{ height: '300px', position: 'relative' }}>
          <canvas id="supplyGapChart" />
        </div>

      </div>

      {/* ── Table card ── */}
      <div className="sg-table-card" style={{
        background: 'var(--surface)',
        border: '1px solid var(--border)',
        borderRadius: '8px',
        padding: '20px 24px',
        overflowX: 'auto',
        WebkitOverflowScrolling: 'touch',
      }}>
        <p style={{
          fontFamily: 'var(--font-heading)',
          fontSize: '16px',
          fontWeight: 700,
          color: 'var(--text-primary)',
          marginBottom: '16px',
          lineHeight: 1.3,
        }}>
          The housing shortage buildup grew in every era — even when building picked up
        </p>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              <th style={TH_STYLE}>Era</th>
              <th style={TH_STYLE}>Homes built</th>
              <th style={TH_STYLE}>True need</th>
              <th style={TH_STYLE}>Net gap</th>
              <th style={{ ...TH_STYLE, whiteSpace: 'normal' }}>What it meant</th>
            </tr>
          </thead>
          <tbody>
            {TABLE_ROWS.map((row, i) => (
              <tr key={i} style={{ borderBottom: i < TABLE_ROWS.length - 1 ? '1px solid var(--border)' : 'none' }}>
                <td style={{ padding: '12px 16px 12px 0', verticalAlign: 'top', minWidth: '140px' }}>
                  <div style={{
                    fontFamily: 'var(--font-heading)',
                    fontSize: '14px',
                    fontWeight: 700,
                    color: 'var(--text-primary)',
                    lineHeight: 1.2,
                  }}>
                    {row.era}
                  </div>
                  <div style={{
                    fontFamily: 'var(--font-data)',
                    fontSize: '10px',
                    color: '#A09C97',
                    marginTop: '3px',
                  }}>
                    {row.sub}
                  </div>
                </td>
                <td style={{
                  padding: '12px 16px 12px 0',
                  fontFamily: 'var(--font-data)',
                  fontSize: '13px',
                  color: 'var(--text-primary)',
                  verticalAlign: 'top',
                  whiteSpace: 'nowrap',
                }}>
                  {row.built}
                </td>
                <td style={{
                  padding: '12px 16px 12px 0',
                  fontFamily: 'var(--font-data)',
                  fontSize: '13px',
                  color: 'var(--text-primary)',
                  verticalAlign: 'top',
                  whiteSpace: 'nowrap',
                }}>
                  {row.need}
                </td>
                <td style={{ padding: '12px 16px 12px 0', verticalAlign: 'top', whiteSpace: 'nowrap' }}>
                  <span style={{
                    display: 'inline-block',
                    background: 'rgba(184,64,64,0.10)',
                    color: '#8B2E2E',
                    borderRadius: '2px',
                    fontFamily: 'var(--font-data)',
                    fontSize: '11px',
                    padding: '2px 6px',
                  }}>
                    {row.gap}
                  </span>
                </td>
                <td style={{
                  padding: '12px 0 12px 0',
                  fontFamily: 'var(--font-body)',
                  fontSize: '12px',
                  color: '#6B6560',
                  verticalAlign: 'top',
                  lineHeight: 1.55,
                }}>
                  {row.note}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* ── Sources ── */}
      <p className="ftb-source" style={{ marginTop: '16px' }}>Sources: MA DHCD Building Permit Survey, Boston proper, 1997–2024 · U.S. Census Bureau, ACS Table B11001 (Household Type), annual 1-year estimates · EOHLC Housing Needs Assessment · Metro Mayors Coalition. See methodology for demand line construction.</p>

    </section>
  )
}

// ─── Helpers ────────────────────────────────────────────────────────────────

function LegendPill({ children }) {
  return (
    <span style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: '6px',
      padding: '5px 10px',
      background: 'var(--bg)',
      border: '1px solid var(--border)',
      borderRadius: '999px',
      fontFamily: 'var(--font-data)',
      fontSize: '12px',
      color: 'var(--text-secondary)',
      lineHeight: 1,
      whiteSpace: 'nowrap',
    }}>
      {children}
    </span>
  )
}

function EraCard({ row }) {
  return (
    <div style={{
      background: 'var(--surface)',
      border: '1px solid var(--border)',
      borderRadius: '12px',
      padding: '18px 18px 16px',
      boxShadow: '0 1px 2px rgba(28,25,22,0.04)',
    }}>
      <h3 style={{
        fontFamily: 'var(--font-heading)',
        fontSize: '17px',
        fontWeight: 700,
        color: 'var(--text-primary)',
        lineHeight: 1.25,
        margin: '0 0 3px 0',
      }}>
        {row.era}
      </h3>
      <p style={{
        fontFamily: 'var(--font-data)',
        fontSize: '11px',
        letterSpacing: '0.08em',
        textTransform: 'uppercase',
        color: 'var(--text-muted)',
        margin: '0 0 12px 0',
      }}>
        {row.sub}
      </p>
      <p style={{
        fontFamily: 'var(--font-body)',
        fontSize: '14.5px',
        color: 'var(--text-secondary)',
        lineHeight: 1.55,
        margin: '0 0 14px 0',
      }}>
        {row.note}
      </p>
      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr 1fr',
        gap: '8px',
        paddingTop: '12px',
        borderTop: '1px solid var(--border)',
      }}>
        <Metric label="Built"     value={row.built} />
        <Metric label="True need" value={row.need} />
        <Metric label="Net gap"   value={row.gap} negative />
      </div>
    </div>
  )
}

function Metric({ label, value, negative }) {
  return (
    <div>
      <div style={{
        fontFamily: 'var(--font-data)',
        fontSize: '10px',
        letterSpacing: '0.08em',
        textTransform: 'uppercase',
        color: 'var(--text-muted)',
        marginBottom: '5px',
        lineHeight: 1.2,
      }}>
        {label}
      </div>
      {negative ? (
        <span style={{
          display: 'inline-block',
          background: 'rgba(184,64,64,0.10)',
          color: '#8B2E2E',
          borderRadius: '4px',
          fontFamily: 'var(--font-data)',
          fontSize: '13px',
          fontWeight: 600,
          padding: '3px 7px',
        }}>
          {value}
        </span>
      ) : (
        <div style={{
          fontFamily: 'var(--font-data)',
          fontSize: '14px',
          fontWeight: 600,
          color: 'var(--text-primary)',
          whiteSpace: 'nowrap',
        }}>
          {value}
        </div>
      )}
    </div>
  )
}
