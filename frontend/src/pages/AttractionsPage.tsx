import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import toast, { Toaster } from 'react-hot-toast'
import { Sparkles, MapPin, Filter, X, CheckSquare, Loader2, ChevronLeft, AlertTriangle, RefreshCw } from 'lucide-react'

import { PageWrapper } from '../components/layout/PageWrapper'
import { AttractionGrid } from '../components/attractions/AttractionGrid'
import { useTripContext } from '../contexts/TripContext'
import { generateItinerary } from '../services/itineraryApi'

export function AttractionsPage() {
  const navigate = useNavigate()
  const { tripDetails, attractions, selectedIds, toggleAttraction, setItinerary } = useTripContext()
  const [loading, setLoading] = useState(false)
  const [filter, setFilter] = useState('')
  const [apiError, setApiError] = useState<string | null>(null)

  // Guard — redirect if no data
  if (!tripDetails || attractions.length === 0) {
    navigate('/plan')
    return null
  }

  const selectedCount = selectedIds.size
  const maxAllowed = (tripDetails.trip_days || 0) * (tripDetails.places_per_day || 0)
  const isOverMax = selectedCount > maxAllowed
  const isUnder = selectedCount < 1
  const isReady = selectedCount >= 1 && !isOverMax

  let validationMessage = ""
  if (isOverMax) {
    const overSelected = selectedCount - maxAllowed
    validationMessage = `Too many selected. Please deselect ${overSelected} attraction${overSelected !== 1 ? 's' : ''}.`
  } else if (isUnder) {
    validationMessage = `Select at least 1 attraction to continue.`
  } else {
    validationMessage = `Ready! Gemini will build your ${tripDetails.trip_days}-day plan.`
  }

  const categories = Array.from(new Set(attractions.map(a => a.category))).sort()
  const [activeCategory, setActiveCategory] = useState<string>('All')

  const filtered = attractions.filter(a => {
    const matchCat = activeCategory === 'All' || a.category === activeCategory
    const matchSearch = !filter || a.name.toLowerCase().includes(filter.toLowerCase())
    return matchCat && matchSearch
  })

  const handleGenerate = async () => {
    if (!isReady) {
      toast.error(validationMessage)
      return
    }

    const selected = attractions.filter(a => selectedIds.has(a.id))
    setLoading(true)
    setApiError(null)

    try {
      const itinerary = await generateItinerary({
        ...tripDetails,
        selected_attractions: selected,
        places_per_day: tripDetails.places_per_day,
      })
      setItinerary(itinerary)
      navigate('/itinerary')
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to generate itinerary'
      setApiError(msg)
      toast.error(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <PageWrapper>
      <Toaster position="top-right" toastOptions={{ style: { background: '#1e1b4b', color: 'white', border: '1px solid rgba(139,92,246,0.3)' } }} />

      {/* Loading overlay */}
      <AnimatePresence>
        {loading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            style={{
              position: 'fixed', inset: 0, zIndex: 100,
              background: 'rgba(15,10,30,0.92)', backdropFilter: 'blur(12px)',
              display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '1.5rem',
            }}
          >
            <div style={{
              width: '72px', height: '72px', borderRadius: '20px',
              background: 'linear-gradient(135deg, #7c3aed, #4f46e5)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              boxShadow: '0 8px 32px rgba(124,58,237,0.5)',
              animation: 'pulse 2s infinite',
            }}>
              <Sparkles size={32} color="white" />
            </div>
            <div style={{ textAlign: 'center' }}>
              <h3 style={{ fontFamily: 'Outfit, sans-serif', fontSize: '1.5rem', fontWeight: 700, color: 'white', margin: '0 0 0.5rem' }}>
                Generating Your Itinerary
              </h3>
              <p style={{ color: 'rgba(255,255,255,0.5)', margin: 0 }}>
                Gemini is organizing your {selectedCount} selected place{selectedCount !== 1 ? 's' : ''}…
              </p>
            </div>
            <Loader2 size={20} color="rgba(168,85,247,0.8)" style={{ animation: 'spin 1s linear infinite' }} />
          </motion.div>
        )}
      </AnimatePresence>

      <div style={{ maxWidth: '1280px', margin: '0 auto', padding: '2.5rem 1.5rem 8rem' }}>

        {/* Page header */}
        <div style={{ marginBottom: '2rem' }}>
          <button
            onClick={() => navigate('/plan')}
            style={{ display: 'flex', alignItems: 'center', gap: '0.375rem', background: 'none', border: 'none', color: 'rgba(255,255,255,0.45)', cursor: 'pointer', fontSize: '0.85rem', marginBottom: '1rem', padding: 0 }}
          >
            <ChevronLeft size={16} /> Back to form
          </button>
          <h1 style={{ fontFamily: 'Outfit, sans-serif', fontWeight: 800, fontSize: 'clamp(1.5rem, 3vw, 2.25rem)', color: 'white', margin: '0 0 0.5rem' }}>
            Attractions in <span className="gradient-text">{tripDetails.destination}</span>
          </h1>
          <p style={{ color: 'rgba(255,255,255,0.5)', margin: 0, fontSize: '0.95rem' }}>
            {attractions.length} real places found · Select the ones you want to visit
          </p>
        </div>

        {/* Selection Summary Card */}
        <div className="glass" style={{
          padding: '1.5rem',
          marginBottom: '2rem',
          background: 'rgba(255, 255, 255, 0.03)',
          border: '1px solid rgba(139,92,246,0.15)',
        }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1.5rem' }}>
            <div>
              <div style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>Trip Duration</div>
              <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'white', marginTop: '0.25rem' }}>{tripDetails.trip_days} Days</div>
            </div>
            <div>
              <div style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>Travel Pace</div>
              <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'white', marginTop: '0.25rem' }}>{tripDetails.places_per_day} Places / Day</div>
            </div>
            <div>
              <div style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>Max Attractions</div>
              <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#c084fc', marginTop: '0.25rem' }}>{maxAllowed}</div>
            </div>
            <div>
              <div style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>Selected</div>
              <div style={{ 
                fontSize: '1.25rem', 
                fontWeight: 700, 
                color: isReady ? '#10b981' : (isOverMax ? '#ef4444' : '#f59e0b'), 
                marginTop: '0.25rem' 
              }}>
                {selectedCount} / Max {maxAllowed}
              </div>
            </div>
          </div>
          <div style={{ 
            marginTop: '1.25rem', 
            paddingTop: '1rem', 
            borderTop: '1px solid rgba(255,255,255,0.06)',
            fontSize: '0.9rem',
            color: isReady ? '#10b981' : (isOverMax ? '#ef4444' : '#f59e0b'),
            fontWeight: 600,
          }}>
            {validationMessage}
          </div>
          <div style={{ marginTop: '0.5rem', fontSize: '0.78rem', color: 'rgba(255,255,255,0.35)' }}>
            You can select up to {maxAllowed} attractions.
          </div>
        </div>

        {/* Error Display Card */}
        {apiError && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass"
            style={{
              padding: '1.5rem',
              marginBottom: '1.5rem',
              border: '1px solid rgba(239, 68, 68, 0.4)',
              background: 'rgba(239, 68, 68, 0.05)',
              display: 'flex',
              gap: '1rem',
              alignItems: 'flex-start',
            }}
          >
            <div style={{
              background: 'rgba(239, 68, 68, 0.2)',
              borderRadius: '50%',
              padding: '0.5rem',
              color: '#ef4444',
              display: 'flex',
            }}>
              <AlertTriangle size={20} />
            </div>
            <div style={{ flex: 1 }}>
              <h3 style={{ color: '#ef4444', fontSize: '0.95rem', fontWeight: 700, margin: '0 0 0.25rem' }}>
                Itinerary Generation Error
              </h3>
              <p style={{ color: 'rgba(255,255,255,0.7)', fontSize: '0.85rem', margin: '0 0 1rem', lineHeight: 1.4 }}>
                {apiError.includes("API key is not configured") 
                  ? "The Gemini API key is missing. Please configure GEMINI_API_KEY in backend/.env to enable itinerary generation."
                  : apiError}
              </p>
              <div style={{ display: 'flex', gap: '0.75rem' }}>
                <button
                  type="button"
                  onClick={() => handleGenerate()}
                  className="btn-primary"
                  style={{
                    padding: '0.5rem 1rem',
                    fontSize: '0.8rem',
                    background: 'linear-gradient(135deg, #ef4444, #b91c1c)',
                    boxShadow: '0 4px 12px rgba(239,68,68,0.3)',
                    gap: '0.375rem',
                  }}
                >
                  <RefreshCw size={14} /> Retry Generation
                </button>
                <button
                  type="button"
                  onClick={() => setApiError(null)}
                  className="btn-secondary"
                  style={{
                    padding: '0.5rem 1rem',
                    fontSize: '0.8rem',
                    borderColor: 'rgba(255, 255, 255, 0.15)',
                    background: 'rgba(255, 255, 255, 0.04)',
                  }}
                >
                  Dismiss
                </button>
              </div>
            </div>
          </motion.div>
        )}

        {/* Filter bar */}
        <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1.75rem', flexWrap: 'wrap', alignItems: 'center' }}>
          {/* Text search */}
          <div style={{ position: 'relative', flex: '1', minWidth: '200px', maxWidth: '300px' }}>
            <Filter size={15} style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: 'rgba(255,255,255,0.35)' }} />
            <input
              placeholder="Filter by name…"
              value={filter}
              onChange={e => setFilter(e.target.value)}
              style={{
                width: '100%', padding: '0.625rem 0.75rem 0.625rem 2.25rem',
                background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: '0.625rem', color: 'white', fontSize: '0.875rem',
                outline: 'none', fontFamily: 'Inter, sans-serif',
              }}
            />
            {filter && (
              <button onClick={() => setFilter('')} style={{ position: 'absolute', right: '0.75rem', top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', color: 'rgba(255,255,255,0.4)', display: 'flex' }}>
                <X size={14} />
              </button>
            )}
          </div>

          {/* Category chips */}
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            {['All', ...categories].map(cat => (
              <button
                key={cat}
                id={`filter-${cat.toLowerCase().replace(/\s+/g, '-')}`}
                onClick={() => setActiveCategory(cat)}
                style={{
                  padding: '0.375rem 0.875rem',
                  borderRadius: '9999px',
                  border: activeCategory === cat ? '1px solid rgba(168,85,247,0.6)' : '1px solid rgba(255,255,255,0.1)',
                  background: activeCategory === cat ? 'rgba(139,92,246,0.2)' : 'rgba(255,255,255,0.04)',
                  color: activeCategory === cat ? '#c084fc' : 'rgba(255,255,255,0.55)',
                  fontSize: '0.78rem', fontWeight: 500, cursor: 'pointer',
                  transition: 'all 0.15s',
                }}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>

        {/* Results count */}
        <p style={{ color: 'rgba(255,255,255,0.35)', fontSize: '0.8rem', marginBottom: '1.25rem' }}>
          Showing {filtered.length} of {attractions.length} attractions
        </p>

        {/* Grid */}
        <AttractionGrid
          attractions={filtered}
          selectedIds={selectedIds}
          onToggle={toggleAttraction}
        />

        {filtered.length === 0 && (
          <div style={{ textAlign: 'center', padding: '4rem', color: 'rgba(255,255,255,0.4)' }}>
            <MapPin size={40} style={{ marginBottom: '1rem', opacity: 0.3 }} />
            <p>No attractions match your filter.</p>
          </div>
        )}
      </div>

      {/* Sticky bottom bar */}
      <AnimatePresence>
        <motion.div
          initial={{ y: 80, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ type: 'spring', stiffness: 400, damping: 30 }}
          style={{
            position: 'fixed', bottom: 0, left: 0, right: 0, zIndex: 50,
            background: 'rgba(15,10,30,0.9)', backdropFilter: 'blur(20px)',
            borderTop: '1px solid rgba(139,92,246,0.25)',
            padding: '1rem 1.5rem',
          }}
        >
          <div style={{ maxWidth: '1280px', margin: '0 auto', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '1rem', flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <div style={{
                width: '36px', height: '36px', borderRadius: '10px',
                background: 'linear-gradient(135deg, #7c3aed, #4f46e5)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                <CheckSquare size={18} color="white" />
              </div>
              <div>
                <div style={{ fontWeight: 700, color: 'white', fontSize: '0.95rem' }}>
                  {selectedCount} attraction{selectedCount !== 1 ? 's' : ''} selected
                </div>
                <div style={{ 
                  fontSize: '0.8rem', 
                  color: isReady ? '#10b981' : (isOverMax ? '#ef4444' : '#f59e0b'),
                  fontWeight: 500,
                  marginTop: '0.125rem'
                }}>
                  {validationMessage}
                </div>
              </div>
            </div>
            <button
              id="generate-plan-btn"
              onClick={handleGenerate}
              disabled={!isReady || loading}
              className="btn-primary"
              style={{ fontSize: '1rem', padding: '0.875rem 2rem' }}
            >
              <Sparkles size={18} /> Generate AI Plan
            </button>
          </div>
        </motion.div>
      </AnimatePresence>
    </PageWrapper>
  )
}
