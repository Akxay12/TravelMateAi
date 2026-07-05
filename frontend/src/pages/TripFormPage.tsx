import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import toast, { Toaster } from 'react-hot-toast'
import {
  MapPin, Calendar, IndianRupee, Users, Compass, Search,
  Loader2, AlertTriangle, RefreshCw, Clock
} from 'lucide-react'

import { PageWrapper } from '../components/layout/PageWrapper'
import { useTripContext } from '../contexts/TripContext'
import type { TravelStyle, TripDetails } from '../contexts/TripContext'
import { searchAttractions } from '../services/attractionsApi'

const TRAVEL_STYLES: { value: TravelStyle; label: string; desc: string; emoji: string }[] = [
  { value: 'budget', label: 'Budget', desc: 'Hostels, street food, free attractions', emoji: '🎒' },
  { value: 'standard', label: 'Standard', desc: 'Mid-range hotels & restaurants', emoji: '🏨' },
  { value: 'luxury', label: 'Luxury', desc: 'Premium stays & fine dining', emoji: '✨' },
]

interface FormState {
  destination: string
  start_date: string
  end_date: string
  budget: string
  travelers: string
  travel_style: TravelStyle
  places_per_day: string
  interests: string
}

const INITIAL_FORM: FormState = {
  destination: '',
  start_date: '',
  end_date: '',
  budget: '',
  travelers: '2',
  travel_style: 'standard',
  places_per_day: '4',
  interests: '',
}

const calculateTripDays = (start: string, end: string): number => {
  if (!start || !end) return 0
  const s = new Date(start)
  const e = new Date(end)
  const utc1 = Date.UTC(s.getFullYear(), s.getMonth(), s.getDate())
  const utc2 = Date.UTC(e.getFullYear(), e.getMonth(), e.getDate())
  return Math.floor((utc2 - utc1) / (1000 * 60 * 60 * 24)) + 1
}

function InputWrapper({ icon, children }: { icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <div style={{ position: 'relative' }}>
      <span style={{
        position: 'absolute', left: '0.875rem', top: '50%', transform: 'translateY(-50%)',
        color: 'rgba(255,255,255,0.35)', pointerEvents: 'none', display: 'flex',
      }}>
        {icon}
      </span>
      {children}
    </div>
  )
}

export function TripFormPage() {
  const navigate = useNavigate()
  const { setTripDetails, setAttractions } = useTripContext()
  const [form, setForm] = useState<FormState>(INITIAL_FORM)
  const [loading, setLoading] = useState(false)
  const [apiError, setApiError] = useState<string | null>(null)

  const update = (field: keyof FormState, value: string) =>
    setForm(prev => ({ ...prev, [field]: value }))

  const validate = (): string | null => {
    if (!form.destination.trim()) return 'Destination is required'
    if (!form.start_date) return 'Start date is required'
    if (!form.end_date) return 'End date is required'
    if (form.end_date < form.start_date) return 'End date must be after start date'
    if (!form.budget || Number(form.budget) <= 0) return 'Budget must be greater than 0'
    if (!form.travelers || Number(form.travelers) < 1) return 'At least 1 traveler required'
    return null
  }

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault()
    const error = validate()
    if (error) { toast.error(error); return }

    setLoading(true)
    setApiError(null)
    const tripDays = calculateTripDays(form.start_date, form.end_date)
    const placesPerDay = Number(form.places_per_day)

    const details: TripDetails = {
      destination: form.destination.trim(),
      start_date: form.start_date,
      end_date: form.end_date,
      budget: Number(form.budget),
      travelers: Number(form.travelers),
      travel_style: form.travel_style,
      places_per_day: placesPerDay,
      trip_days: tripDays,
      interests: form.interests.trim() || undefined,
    }

    try {
      setTripDetails(details)
      const data = await searchAttractions(details)
      setAttractions(data.attractions)
      navigate('/attractions')
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to find attractions'
      setApiError(msg)
      toast.error(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <PageWrapper>
      <Toaster position="top-right" toastOptions={{ style: { background: '#1e1b4b', color: 'white', border: '1px solid rgba(139,92,246,0.3)' } }} />

      <div style={{ minHeight: 'calc(100vh - 64px)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '3rem 1.5rem' }}>
        {/* Background decoration */}
        <div className="orb orb-purple" style={{ position: 'fixed', width: '400px', height: '400px', top: '10%', right: '-100px', pointerEvents: 'none' }} />
        <div className="orb orb-indigo" style={{ position: 'fixed', width: '300px', height: '300px', bottom: '5%', left: '-80px', pointerEvents: 'none' }} />

        <div style={{ width: '100%', maxWidth: '640px', position: 'relative', zIndex: 1 }}>
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: -12 }}
            animate={{ opacity: 1, y: 0 }}
            style={{ textAlign: 'center', marginBottom: '2.5rem' }}
          >
            <div style={{
              display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
              width: '56px', height: '56px', borderRadius: '16px',
              background: 'linear-gradient(135deg, #7c3aed, #4f46e5)',
              boxShadow: '0 8px 24px rgba(124,58,237,0.4)',
              marginBottom: '1.25rem',
            }}>
              <Compass size={26} color="white" />
            </div>
            <h1 style={{ fontFamily: 'Outfit, sans-serif', fontWeight: 800, fontSize: '2rem', color: 'white', margin: '0 0 0.5rem' }}>
              Plan Your Trip
            </h1>
            <p style={{ color: 'rgba(255,255,255,0.5)', margin: 0, fontSize: '0.95rem' }}>
              Tell us where you're going and we'll find real attractions for you.
            </p>
          </motion.div>

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
                  Backend Connection Error
                </h3>
                <p style={{ color: 'rgba(255,255,255,0.7)', fontSize: '0.85rem', margin: '0 0 1rem', lineHeight: 1.4 }}>
                  {apiError === 'Failed to fetch' 
                    ? 'The backend server is currently unreachable. Please make sure start_backend.bat is running.'
                    : apiError}
                </p>
                <button
                  type="button"
                  onClick={() => handleSubmit()}
                  className="btn-primary"
                  style={{
                    padding: '0.5rem 1rem',
                    fontSize: '0.8rem',
                    background: 'linear-gradient(135deg, #ef4444, #b91c1c)',
                    boxShadow: '0 4px 12px rgba(239,68,68,0.3)',
                    gap: '0.375rem',
                  }}
                >
                  <RefreshCw size={14} /> Retry Connection
                </button>
              </div>
            </motion.div>
          )}

          {/* Form card */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="glass"
            style={{ padding: '2rem' }}
          >
            <form onSubmit={handleSubmit}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>

                {/* Destination */}
                <div>
                  <label className="form-label" htmlFor="destination">Destination</label>
                  <InputWrapper icon={<MapPin size={16} />}>
                    <input
                      id="destination"
                      className="form-input"
                      type="text"
                      placeholder="Enter any city, town, hill station, or landmark..."
                      value={form.destination}
                      onChange={e => update('destination', e.target.value)}
                      disabled={loading}
                      autoFocus
                    />
                  </InputWrapper>
                </div>

                {/* Date row */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                  <div>
                    <label className="form-label" htmlFor="start_date">Start Date</label>
                    <InputWrapper icon={<Calendar size={16} />}>
                      <input
                        id="start_date"
                        className="form-input"
                        type="date"
                        value={form.start_date}
                        onChange={e => update('start_date', e.target.value)}
                        disabled={loading}
                        min={new Date().toISOString().split('T')[0]}
                      />
                    </InputWrapper>
                  </div>
                  <div>
                    <label className="form-label" htmlFor="end_date">End Date</label>
                    <InputWrapper icon={<Calendar size={16} />}>
                      <input
                        id="end_date"
                        className="form-input"
                        type="date"
                        value={form.end_date}
                        onChange={e => update('end_date', e.target.value)}
                        disabled={loading}
                        min={form.start_date || new Date().toISOString().split('T')[0]}
                      />
                    </InputWrapper>
                  </div>
                </div>

                {/* Budget + Travelers row */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                  <div>
                    <label className="form-label" htmlFor="budget">Total Budget (INR, ₹)</label>
                    <InputWrapper icon={<IndianRupee size={16} />}>
                      <input
                        id="budget"
                        className="form-input"
                        type="number"
                        placeholder="e.g. 50000"
                        value={form.budget}
                        onChange={e => update('budget', e.target.value)}
                        disabled={loading}
                        min={1}
                      />
                    </InputWrapper>
                  </div>
                  <div>
                    <label className="form-label" htmlFor="travelers">Travelers</label>
                    <InputWrapper icon={<Users size={16} />}>
                      <input
                        id="travelers"
                        className="form-input"
                        type="number"
                        value={form.travelers}
                        onChange={e => update('travelers', e.target.value)}
                        disabled={loading}
                        min={1}
                        max={50}
                      />
                    </InputWrapper>
                  </div>
                </div>

                {/* Travel Style */}
                <div>
                  <label className="form-label">Travel Style</label>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.625rem' }}>
                    {TRAVEL_STYLES.map(style => (
                      <button
                        key={style.value}
                        type="button"
                        id={`style-${style.value}`}
                        onClick={() => {
                          const defaultPace = style.value === 'budget' ? '5' : (style.value === 'luxury' ? '2' : '4');
                          setForm(prev => ({
                            ...prev,
                            travel_style: style.value,
                            places_per_day: defaultPace
                          }));
                        }}
                        disabled={loading}
                        style={{
                          padding: '0.875rem 0.5rem',
                          borderRadius: '0.75rem',
                          border: form.travel_style === style.value
                            ? '2px solid rgba(168,85,247,0.7)'
                            : '1px solid rgba(255,255,255,0.1)',
                          background: form.travel_style === style.value
                            ? 'rgba(139,92,246,0.15)'
                            : 'rgba(255,255,255,0.04)',
                          cursor: 'pointer',
                          textAlign: 'center',
                          transition: 'all 0.2s',
                        }}
                      >
                        <div style={{ fontSize: '1.25rem', marginBottom: '0.25rem' }}>{style.emoji}</div>
                        <div style={{ fontSize: '0.8rem', fontWeight: 700, color: form.travel_style === style.value ? '#c084fc' : 'rgba(255,255,255,0.7)' }}>
                          {style.label}
                        </div>
                        <div style={{ fontSize: '0.65rem', color: 'rgba(255,255,255,0.4)', marginTop: '0.125rem', lineHeight: 1.3 }}>
                          {style.desc}
                        </div>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Places to Visit Per Day */}
                <div>
                  <label className="form-label" htmlFor="places_per_day">Places to Visit Per Day</label>
                  <InputWrapper icon={<Clock size={16} />}>
                    <select
                      id="places_per_day"
                      className="form-input"
                      value={form.places_per_day}
                      onChange={e => update('places_per_day', e.target.value)}
                      disabled={loading}
                      style={{ appearance: 'auto' as any, WebkitAppearance: 'auto' as any, background: 'rgba(255, 255, 255, 0.06)', color: 'white', paddingRight: '2rem' }}
                    >
                      <option value="2">2</option>
                      <option value="3">3</option>
                      <option value="4">4</option>
                      <option value="5">5</option>
                      <option value="6">6</option>
                    </select>
                  </InputWrapper>
                </div>

                {/* Interests */}
                <div>
                  <label className="form-label" htmlFor="interests">Interests</label>
                  <InputWrapper icon={<Compass size={16} />}>
                    <input
                      id="interests"
                      className="form-input"
                      type="text"
                      placeholder="e.g. Museums, parks, historic sites, local food"
                      value={form.interests}
                      onChange={e => update('interests', e.target.value)}
                      disabled={loading}
                    />
                  </InputWrapper>
                </div>

                {/* Submit */}
                <button
                  id="find-attractions-btn"
                  type="submit"
                  className="btn-primary"
                  disabled={loading}
                  style={{ justifyContent: 'center', marginTop: '0.5rem', fontSize: '1rem', padding: '1rem' }}
                >
                  {loading ? (
                    <><Loader2 size={18} className="animate-spin" /> Generating Attractions...</>
                  ) : (
                    <><Search size={18} /> Generate Attractions</>
                  )}
                </button>

              </div>
            </form>
          </motion.div>
        </div>
      </div>
    </PageWrapper>
  )
}

