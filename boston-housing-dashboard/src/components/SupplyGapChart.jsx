import { useEffect, useRef } from 'react'

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

export default function SupplyGapChart() {
  const chartRef = useRef(null)

  useEffect(() => {
    const initChart = () => {
      const Chart = window.Chart
      if (!Chart) return
      const canvas = document.getElementById('supplyGapChart')
      if (!canvas) return
      const existing = Chart.getChart(canvas)
      if (existing) existing.destroy()
      chartRef.current = new Chart(canvas, {
        type: 'line',
        data: {
          labels: YEARS,
          datasets: [
            {
              label: 'Homes permitted',
              data: SUPPLY,
              borderColor: '#3B6B8A',
              borderWidth: 2,
              pointRadius: 3,
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
          plugins: {
            legend: { display: false },
            tooltip: {
              backgroundColor: 'rgba(28,25,22,0.92)',
              titleFont: { family: 'Oswald', size: 13 },
              bodyFont: { family: 'Lato', size: 12 },
              footerFont: { family: 'Lato', size: 12 },
              footerColor: 'rgba(255,255,255,0.75)',
              padding: 10,
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
                font: { family: 'DM Mono', size: 11 },
                color: '#6B6560',
                maxRotation: 45,
              },
            },
            y: {
              min: 0,
              max: 6500,
              title: {
                display: true,
                text: 'UNITS / YEAR',
                font: { family: 'DM Mono', size: 10 },
                color: '#A09C97',
              },
              ticks: {
                font: { family: 'DM Mono', size: 11 },
                color: '#6B6560',
                callback: val => val.toLocaleString(),
              },
              grid: {
                color: 'rgba(226,221,214,0.7)',
              },
            },
          },
        },
      })
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
  }, [])

  return (
    <section style={{ maxWidth: '1160px', margin: '0 auto', padding: '56px 48px 48px' }}>

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
      <h2 style={{
        fontFamily: 'var(--font-heading)',
        fontSize: '28px',
        fontWeight: 500,
        letterSpacing: '-0.3px',
        lineHeight: 1.2,
        color: 'var(--text-primary)',
        marginBottom: '10px',
      }}>
        Even in Boston's best building years, we never dug out of the hole
      </h2>

      {/* ── Subhead ── */}
      <p style={{
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
      <div style={{ display: 'flex', gap: '16px', marginBottom: '24px', flexWrap: 'wrap' }}>
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
              fontWeight: 300,
              letterSpacing: '-0.5px',
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
      <div style={{
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

        {/* Source footnote */}
        <p style={{
          fontFamily: 'var(--font-body)',
          fontSize: '0.75rem',
          color: '#A09C97',
          marginTop: '12px',
          lineHeight: 1.5,
          paddingLeft: '4px',
        }}>
          MA DHCD Building Permit Survey (Boston proper) · U.S. Census ACS B11001 · EOHLC Housing Needs
          Assessment · Metro Mayors Coalition. See methodology for demand line construction.
        </p>
      </div>

      {/* ── Table card ── */}
      <div style={{
        background: 'var(--surface)',
        border: '1px solid var(--border)',
        borderRadius: '8px',
        padding: '20px 24px',
        overflowX: 'auto',
      }}>
        <p style={{
          fontFamily: 'var(--font-heading)',
          fontSize: '16px',
          fontWeight: 500,
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
                    fontWeight: 500,
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
      <p className="ftb-source" style={{ marginTop: '16px' }}>Source: MA DHCD Building Permit Survey, Boston proper, 1997–2024 — supply line</p>
      <p className="ftb-source">U.S. Census Bureau, ACS Table B11001 (Household Type), annual 1-year estimates — household formation baseline</p>

    </section>
  )
}
