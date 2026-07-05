import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { MapPin, Calendar, Users, IndianRupee, Printer, ArrowLeft, RefreshCw, CheckCircle2 } from 'lucide-react'
import { PageWrapper } from '../components/layout/PageWrapper'
import { DayCard } from '../components/itinerary/DayCard'
import { useTripContext } from '../contexts/TripContext'

export function ItineraryPage() {
  const navigate = useNavigate()
  const { itinerary, tripDetails, selectedIds, resetAll } = useTripContext()

  if (!itinerary || !tripDetails) {
    navigate('/plan')
    return null
  }

  const tripStyleLabel: Record<string, string> = { budget: '🎒 Budget', standard: '🏨 Standard', luxury: '✨ Luxury' }

  return (
    <PageWrapper>
      <div style={{ maxWidth: '900px', margin: '0 auto', padding: '2.5rem 1.5rem 5rem' }}>

        {/* Back button */}
        <button
          onClick={() => navigate('/attractions')}
          style={{ display: 'flex', alignItems: 'center', gap: '0.375rem', background: 'none', border: 'none', color: 'rgba(255,255,255,0.45)', cursor: 'pointer', fontSize: '0.85rem', marginBottom: '1.75rem', padding: 0 }}
        >
          <ArrowLeft size={15} /> Back to attractions
        </button>

        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -12 }}
          animate={{ opacity: 1, y: 0 }}
          style={{ marginBottom: '2rem' }}
        >
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                <CheckCircle2 size={18} color="#a855f7" />
                <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#a855f7', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                  AI Itinerary Generated
                </span>
              </div>
              <h1 style={{ fontFamily: 'Outfit, sans-serif', fontWeight: 800, fontSize: 'clamp(1.75rem, 4vw, 2.5rem)', color: 'white', margin: '0 0 0.5rem' }}>
                {itinerary.destination}
              </h1>
              <p style={{ color: 'rgba(255,255,255,0.5)', margin: 0 }}>
                {itinerary.total_days}-day itinerary · {selectedIds.size} attraction{selectedIds.size !== 1 ? 's' : ''} organized
              </p>
            </div>

            <div style={{ display: 'flex', gap: '0.75rem' }}>
              <button
                onClick={() => window.print()}
                className="btn-secondary"
                style={{ padding: '0.625rem 1.25rem', fontSize: '0.875rem' }}
                id="print-itinerary-btn"
              >
                <Printer size={15} /> Print
              </button>
              <button
                onClick={() => { resetAll(); navigate('/') }}
                className="btn-secondary"
                style={{ padding: '0.625rem 1.25rem', fontSize: '0.875rem' }}
                id="new-trip-btn"
              >
                <RefreshCw size={15} /> New Trip
              </button>
            </div>
          </div>
        </motion.div>

        {/* Trip summary card */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="glass"
          style={{ padding: '1.25rem 1.5rem', marginBottom: '2rem', display: 'flex', flexWrap: 'wrap', gap: '1.5rem' }}
        >
          {[
            { icon: <Calendar size={15} />, label: 'Dates', value: `${tripDetails.start_date} → ${tripDetails.end_date}` },
            { icon: <Users size={15} />, label: 'Travelers', value: String(tripDetails.travelers) },
            { icon: <IndianRupee size={15} />, label: 'Budget', value: `₹${tripDetails.budget.toLocaleString('en-IN')}` },
            { icon: <MapPin size={15} />, label: 'Style', value: tripStyleLabel[tripDetails.travel_style] ?? tripDetails.travel_style },
          ].map(item => (
            <div key={item.label} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{ color: 'rgba(255,255,255,0.35)' }}>{item.icon}</span>
              <span style={{ fontSize: '0.8rem', color: 'rgba(255,255,255,0.4)' }}>{item.label}:</span>
              <span style={{ fontSize: '0.875rem', fontWeight: 600, color: 'rgba(255,255,255,0.85)' }}>{item.value}</span>
            </div>
          ))}
        </motion.div>

        {/* Day cards */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {itinerary.days.map((day, i) => (
            <motion.div
              key={day.day_number}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.15 + i * 0.07 }}
            >
              <DayCard day={day} isFirst={i === 0} />
            </motion.div>
          ))}
        </div>

        {/* Rich Final Summary Section */}
        {(itinerary.overview || itinerary.budget_summary || itinerary.weather_summary || itinerary.final_summary) && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 + itinerary.days.length * 0.07 }}
            className="glass"
            style={{ marginTop: '2.5rem', padding: '2rem', display: 'flex', flexDirection: 'column', gap: '2rem' }}
          >
            <h2 style={{ fontFamily: 'Outfit, sans-serif', fontWeight: 800, fontSize: '1.5rem', color: 'white', margin: 0, borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '0.75rem' }}>
              🎯 Trip Final Summary & Overview
            </h2>

            {/* Trip Overview */}
            {itinerary.overview && (
              <div>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'white', marginBottom: '0.5rem' }}>Trip Overview</h3>
                <p style={{ color: 'rgba(255,255,255,0.7)', fontSize: '0.9rem', lineHeight: 1.6, margin: 0 }}>
                  {itinerary.overview}
                </p>
              </div>
            )}

            {/* Budget Summary & Breakdown */}
            {itinerary.budget_summary && (
              <div>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'white', marginBottom: '0.75rem' }}>Estimated Trip Budget</h3>
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                  gap: '1rem',
                  background: 'rgba(255,255,255,0.02)',
                  border: '1px solid rgba(255,255,255,0.05)',
                  padding: '1.25rem',
                  borderRadius: '0.75rem'
                }}>
                  <div>
                    <span style={{ fontSize: '0.8rem', color: 'rgba(255,255,255,0.5)' }}>Accommodation</span>
                    <div style={{ fontSize: '1.15rem', fontWeight: 700, color: 'white' }}>₹{itinerary.budget_summary.accommodation.toLocaleString('en-IN')}</div>
                  </div>
                  <div>
                    <span style={{ fontSize: '0.8rem', color: 'rgba(255,255,255,0.5)' }}>Food</span>
                    <div style={{ fontSize: '1.15rem', fontWeight: 700, color: 'white' }}>₹{itinerary.budget_summary.food.toLocaleString('en-IN')}</div>
                  </div>
                  <div>
                    <span style={{ fontSize: '0.8rem', color: 'rgba(255,255,255,0.5)' }}>Transportation</span>
                    <div style={{ fontSize: '1.15rem', fontWeight: 700, color: 'white' }}>₹{itinerary.budget_summary.transport.toLocaleString('en-IN')}</div>
                  </div>
                  <div>
                    <span style={{ fontSize: '0.8rem', color: 'rgba(255,255,255,0.5)' }}>Attraction Tickets</span>
                    <div style={{ fontSize: '1.15rem', fontWeight: 700, color: 'white' }}>₹{itinerary.budget_summary.tickets.toLocaleString('en-IN')}</div>
                  </div>
                  <div>
                    <span style={{ fontSize: '0.8rem', color: 'rgba(255,255,255,0.5)' }}>Miscellaneous</span>
                    <div style={{ fontSize: '1.15rem', fontWeight: 700, color: 'white' }}>₹{itinerary.budget_summary.miscellaneous.toLocaleString('en-IN')}</div>
                  </div>
                  <div style={{ borderLeft: '1px solid rgba(255,255,255,0.1)', paddingLeft: '1rem' }}>
                    <span style={{ fontSize: '0.8rem', color: '#c084fc', fontWeight: 600 }}>Estimated Total</span>
                    <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#c084fc' }}>₹{itinerary.budget_summary.total.toLocaleString('en-IN')}</div>
                  </div>
                  <div style={{ borderLeft: '1px solid rgba(255,255,255,0.1)', paddingLeft: '1rem' }}>
                    <span style={{ fontSize: '0.8rem', color: 'rgba(255,255,255,0.5)' }}>Remaining Budget</span>
                    <div style={{ fontSize: '1.15rem', fontWeight: 700, color: itinerary.budget_summary.remaining >= 0 ? '#4ade80' : '#f87171' }}>
                      ₹{itinerary.budget_summary.remaining.toLocaleString('en-IN')}
                    </div>
                  </div>
                  <div>
                    <span style={{ fontSize: '0.8rem', color: 'rgba(255,255,255,0.5)' }}>Budget Status</span>
                    <div style={{
                      fontSize: '0.8rem',
                      fontWeight: 700,
                      color: itinerary.budget_summary.status.toUpperCase().includes('OVER') ? '#ef4444' : itinerary.budget_summary.status.toUpperCase().includes('NEAR') ? '#f59e0b' : '#10b981',
                      marginTop: '0.25rem'
                    }}>
                      {itinerary.budget_summary.status.replace('_', ' ')}
                    </div>
                  </div>
                </div>
                {itinerary.budget_notes && (
                  <p style={{ marginTop: '0.75rem', color: 'rgba(255,255,255,0.5)', fontSize: '0.825rem', fontStyle: 'italic', lineHeight: 1.4 }}>
                    Note: {itinerary.budget_notes}
                  </p>
                )}
              </div>
            )}

            {/* Weather Summary */}
            {itinerary.weather_summary && (
              <div>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'white', marginBottom: '0.75rem' }}>Weather Forecast</h3>
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                  gap: '1rem',
                  background: 'rgba(255,255,255,0.02)',
                  border: '1px solid rgba(255,255,255,0.05)',
                  padding: '1.25rem',
                  borderRadius: '0.75rem',
                  marginBottom: '1rem'
                }}>
                  <div>
                    <span style={{ fontSize: '0.8rem', color: 'rgba(255,255,255,0.5)' }}>Condition</span>
                    <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'white' }}>{itinerary.weather_summary.condition}</div>
                  </div>
                  <div>
                    <span style={{ fontSize: '0.8rem', color: 'rgba(255,255,255,0.5)' }}>Temperature Range</span>
                    <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'white' }}>{itinerary.weather_summary.temperature_range}</div>
                  </div>
                  <div>
                    <span style={{ fontSize: '0.8rem', color: 'rgba(255,255,255,0.5)' }}>Rain Probability</span>
                    <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'white' }}>{itinerary.weather_summary.rain_probability}</div>
                  </div>
                  <div>
                    <span style={{ fontSize: '0.8rem', color: 'rgba(255,255,255,0.5)' }}>Wind Speed</span>
                    <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'white' }}>{itinerary.weather_summary.wind_speed}</div>
                  </div>
                  <div>
                    <span style={{ fontSize: '0.8rem', color: 'rgba(255,255,255,0.5)' }}>Humidity</span>
                    <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'white' }}>{itinerary.weather_summary.humidity}</div>
                  </div>
                  <div>
                    <span style={{ fontSize: '0.8rem', color: 'rgba(255,255,255,0.5)' }}>Risk Level</span>
                    <div style={{
                      fontSize: '0.85rem',
                      fontWeight: 700,
                      color: itinerary.weather_summary.risk_level === 'HIGH' ? '#ef4444' : itinerary.weather_summary.risk_level === 'MODERATE' ? '#f59e0b' : '#10b981',
                      marginTop: '0.25rem'
                    }}>
                      {itinerary.weather_summary.risk_level}
                    </div>
                  </div>
                </div>

                {/* Advisories */}
                {itinerary.weather_summary.advisories && itinerary.weather_summary.advisories.length > 0 && (
                  <div style={{ marginBottom: '1rem' }}>
                    <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'rgba(255,255,255,0.7)', display: 'block', marginBottom: '0.375rem' }}>
                      Travel Advisory
                    </span>
                    <ul style={{ margin: 0, paddingLeft: '1.25rem', color: 'rgba(255,255,255,0.6)', fontSize: '0.85rem', lineHeight: 1.5 }}>
                      {itinerary.weather_summary.advisories.map((adv, idx) => (
                        <li key={idx}>• {adv}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Packing Checklist */}
                {itinerary.weather_summary.packing_checklist && itinerary.weather_summary.packing_checklist.length > 0 && (
                  <div>
                    <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'rgba(255,255,255,0.7)', display: 'block', marginBottom: '0.5rem' }}>
                      Packing Checklist
                    </span>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                      {itinerary.weather_summary.packing_checklist.map((item, idx) => (
                        <span key={idx} style={{
                          fontSize: '0.8rem',
                          background: 'rgba(16,185,129,0.1)',
                          border: '1px solid rgba(16,185,129,0.2)',
                          color: '#34d399',
                          padding: '0.25rem 0.625rem',
                          borderRadius: '2rem',
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '0.25rem'
                        }}>
                          ✔ {item}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                {itinerary.weather_notes && (
                  <p style={{ marginTop: '0.75rem', color: 'rgba(255,255,255,0.5)', fontSize: '0.825rem', fontStyle: 'italic', lineHeight: 1.4 }}>
                    Note: {itinerary.weather_notes}
                  </p>
                )}
              </div>
            )}

            {/* Important Travel Advice */}
            {itinerary.important_travel_advice && itinerary.important_travel_advice.length > 0 && (
              <div>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'white', marginBottom: '0.5rem' }}>Important Travel Advice</h3>
                <ul style={{ margin: 0, paddingLeft: '1.25rem', color: 'rgba(255,255,255,0.7)', fontSize: '0.9rem', lineHeight: 1.6 }}>
                  {itinerary.important_travel_advice.map((advice, idx) => (
                    <li key={idx}>{advice}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Emergency Tips (if Risk Level is HIGH) */}
            {itinerary.emergency_tips && itinerary.emergency_tips.length > 0 && (
              <div style={{
                background: 'rgba(239,68,68,0.08)',
                border: '1px solid rgba(239,68,68,0.2)',
                padding: '1.25rem',
                borderRadius: '0.75rem'
              }}>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f87171', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  ⚠️ Emergency Tips
                </h3>
                <ul style={{ margin: 0, paddingLeft: '1.25rem', color: '#fca5a5', fontSize: '0.9rem', lineHeight: 1.6 }}>
                  {itinerary.emergency_tips.map((tip, idx) => (
                    <li key={idx}>{tip}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Final Wrap-Up */}
            {itinerary.final_summary && (
              <div>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'white', marginBottom: '0.5rem' }}>Wrap-up</h3>
                <p style={{ color: 'rgba(255,255,255,0.7)', fontSize: '0.9rem', lineHeight: 1.6, margin: 0 }}>
                  {itinerary.final_summary}
                </p>
              </div>
            )}
          </motion.div>
        )}

        {/* Footer note */}
        <div style={{
          marginTop: '2.5rem', padding: '1rem 1.25rem',
          background: 'rgba(255,255,255,0.03)',
          border: '1px solid rgba(255,255,255,0.06)',
          borderRadius: '0.75rem',
          fontSize: '0.78rem', color: 'rgba(255,255,255,0.35)', lineHeight: 1.6,
        }}>
          <strong style={{ color: 'rgba(255,255,255,0.55)' }}>Note:</strong> This itinerary was generated by Gemini AI using only the attractions you selected.
          Opening hours and availability may vary. Please verify with each venue before visiting.
        </div>
      </div>
    </PageWrapper>
  )
}
