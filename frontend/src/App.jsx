import { useMemo, useState } from 'react'
import './App.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001'

function normalizeListing(item) {
  const analysis = item.analysis || {
    score: item.is_match ? 70 : 40,
    verdict: item.verdict || 'Older API response: no structured analysis returned.',
    matched: item.is_match ? ['Legacy positive match'] : [],
    missing: item.is_match ? [] : ['Structured evidence unavailable'],
    cautions: ['Start the latest backend to enable full scoring.'],
  }

  return { ...item, analysis }
}

function DetailList({ title, items }) {
  if (!items?.length) return null

  return (
    <div className="detail-list">
      <span>{title}</span>
      <ul>
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  )
}

function App() {
  const [location, setLocation] = useState('Leatherhead, UK')
  const [vibe, setVibe] = useState('Authentic farm stay with sheep or horses nearby, quiet, good Wi-Fi, and not a central city flat.')
  const [checkIn, setCheckIn] = useState('2026-06-01')
  const [checkOut, setCheckOut] = useState('2026-06-05')
  const [guests, setGuests] = useState(2)
  const [maxPrice, setMaxPrice] = useState(160)
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const bestScore = useMemo(
    () => results.reduce((max, item) => Math.max(max, item.analysis?.score || 0), 0),
    [results],
  )

  const handleSearch = async (event) => {
    event.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const response = await fetch(`${API_URL}/search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          location,
          vibe,
          check_in: checkIn || null,
          check_out: checkOut || null,
          guests: Number(guests),
          max_price: maxPrice ? Number(maxPrice) : null,
          limit: 8,
        }),
      })

      if (!response.ok) {
        throw new Error('Search failed. Check that the FastAPI server is running on port 8001.')
      }

      const data = await response.json()
      setResults(data.map(normalizeListing))
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app-shell">
      <main className="container">
        <header className="hero">
          <div className="badge">Open-source stay intelligence</div>
          <h1>Lodgic</h1>
          <p className="subtitle">
            Natural-language Airbnb search that turns fuzzy travel preferences into ranked, explainable shortlists.
          </p>
        </header>

        <section className="workspace">
          <form className="search-box glass-card" onSubmit={handleSearch}>
            <div className="form-header">
              <span>Search setup</span>
              <strong>Explainable ranking</strong>
            </div>

            <div className="input-group destination">
              <label htmlFor="location">Destination</label>
              <input
                id="location"
                value={location}
                onChange={(event) => setLocation(event.target.value)}
                placeholder="Leatherhead, UK"
              />
            </div>

            <div className="input-group vibe">
              <label htmlFor="vibe">Trip intent</label>
              <textarea
                id="vibe"
                value={vibe}
                onChange={(event) => setVibe(event.target.value)}
                placeholder="Quiet cottage with sheep nearby, desk, fireplace, not commercial..."
                rows={5}
              />
            </div>

            <div className="filters">
              <div className="input-group">
                <label htmlFor="check-in">Check-in</label>
                <input id="check-in" type="date" value={checkIn} onChange={(event) => setCheckIn(event.target.value)} />
              </div>
              <div className="input-group">
                <label htmlFor="check-out">Check-out</label>
                <input id="check-out" type="date" value={checkOut} onChange={(event) => setCheckOut(event.target.value)} />
              </div>
              <div className="input-group compact">
                <label htmlFor="guests">Guests</label>
                <input
                  id="guests"
                  type="number"
                  min="1"
                  max="16"
                  value={guests}
                  onChange={(event) => setGuests(event.target.value)}
                />
              </div>
              <div className="input-group compact">
                <label htmlFor="budget">Max/night</label>
                <input
                  id="budget"
                  type="number"
                  min="1"
                  value={maxPrice}
                  onChange={(event) => setMaxPrice(event.target.value)}
                />
              </div>
            </div>

            <button type="submit" disabled={loading}>
              {loading ? 'Ranking stays...' : 'Rank stays'}
            </button>
          </form>

          <aside className="trust-panel glass-card">
            <span>Decision model</span>
            <strong>{results.length ? `${bestScore}/100` : 'Ready'}</strong>
            <p>Scores combine listing text, amenities, review signals when available, and explicit user intent.</p>
            <div className="trust-grid">
              <div>
                <b>Evidence</b>
                <small>What supports the match</small>
              </div>
              <div>
                <b>Gaps</b>
                <small>What is not proven yet</small>
              </div>
              <div>
                <b>Watch</b>
                <small>Booking risks to inspect</small>
              </div>
            </div>
          </aside>
        </section>

        {error && <div className="error-message">{error}</div>}

        {results.length > 0 && (
          <section className="result-summary" aria-live="polite">
            <strong>{results.length} listings analyzed</strong>
            <span>Best match score: {bestScore}/100</span>
          </section>
        )}

        <section className="results-grid">
          {results.map((item) => (
            <article key={item.id} className={`result-card glass-card ${item.is_match ? 'match' : 'no-match'}`}>
              <div className="card-image" style={{ backgroundImage: `url(${item.image})` }}>
                <div className="score-ring">
                  <strong>{item.analysis?.score ?? 0}</strong>
                  <span>match</span>
                </div>
                <div className="price-badge">{item.price}</div>
              </div>

              <div className="card-content">
                <div className="card-heading">
                  <div>
                    <p>{item.room_type || 'Stay'}</p>
                    <h2>{item.name}</h2>
                  </div>
                  {item.rating && <span className="rating">{item.rating.toFixed(2)}</span>}
                </div>

                <p className="verdict">{item.analysis?.verdict || 'No analysis available yet.'}</p>

                <DetailList title="Evidence" items={item.analysis?.matched} />
                <DetailList title="Gaps" items={item.analysis?.missing} />
                <DetailList title="Watch" items={item.analysis?.cautions} />

                <a href={item.url} target="_blank" rel="noopener noreferrer" className="view-link">
                  View on Airbnb
                </a>
              </div>
            </article>
          ))}
        </section>

        {!loading && results.length === 0 && !error && (
          <div className="empty-state">
            Try a highly specific intent: animals nearby, quiet road, work desk, fireplace, walking distance, or no party area.
          </div>
        )}
      </main>
    </div>
  )
}

export default App
