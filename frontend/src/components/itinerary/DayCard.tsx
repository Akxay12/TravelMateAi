import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronDown, Sun, Sunset, Moon, Utensils, Clock, Coffee } from 'lucide-react'
import type { DayPlan, TimeSlotItem } from '../../contexts/TripContext'

interface TimeSlotProps {
  item: TimeSlotItem
}

function TimeSlotRow({ item }: TimeSlotProps) {
  return (
    <div className="time-slot">
      <div style={{
        minWidth: '52px',
        textAlign: 'center',
        padding: '0.25rem 0.5rem',
        background: 'rgba(139,92,246,0.15)',
        borderRadius: '0.5rem',
        border: '1px solid rgba(139,92,246,0.2)',
      }}>
        <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#c084fc' }}>
          {item.suggested_time}
        </span>
      </div>
      <div style={{ flex: 1 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '0.5rem', flexWrap: 'wrap' }}>
          <span style={{ fontWeight: 600, fontSize: '0.9rem', color: 'white' }}>{item.name}</span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', fontSize: '0.75rem', color: 'rgba(255,255,255,0.45)' }}>
            <Clock size={11} /> {item.duration_minutes} min
          </span>
        </div>
        {item.notes && (
          <p style={{ margin: '0.25rem 0 0', fontSize: '0.8rem', color: 'rgba(255,255,255,0.5)', lineHeight: 1.4 }}>
            {item.notes}
          </p>
        )}
      </div>
    </div>
  )
}

interface SectionProps {
  label: string
  icon: React.ReactNode
  items: TimeSlotItem[]
  color: string
}

function DaySection({ label, icon, items, color }: SectionProps) {
  if (items.length === 0) return null
  return (
    <div style={{ marginBottom: '1rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
        <span style={{ color }}>{icon}</span>
        <span style={{ fontSize: '0.8rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color }}>
          {label}
        </span>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        {items.map((item, i) => <TimeSlotRow key={i} item={item} />)}
      </div>
    </div>
  )
}

interface DayCardProps {
  day: DayPlan
  isFirst?: boolean
}

export function DayCard({ day, isFirst }: DayCardProps) {
  const [isOpen, setIsOpen] = useState(isFirst ?? false)

  const totalAttractions = day.morning.length + day.afternoon.length + day.evening.length

  return (
    <div className="day-card">
      {/* Header — always visible, click to expand */}
      <button
        id={`day-${day.day_number}-header`}
        onClick={() => setIsOpen(!isOpen)}
        style={{
          width: '100%', border: 'none', cursor: 'pointer', textAlign: 'left',
          background: 'none', padding: 0,
        }}
      >
        <div className="day-header">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <div style={{
                  width: '40px', height: '40px', borderRadius: '10px',
                  background: 'linear-gradient(135deg, #7c3aed, #4f46e5)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontWeight: 800, fontSize: '1rem', color: 'white',
                  boxShadow: '0 4px 12px rgba(124,58,237,0.4)',
                }}>
                  {day.day_number}
                </div>
                <div>
                  <h3 style={{ margin: 0, fontWeight: 700, fontSize: '1.05rem', color: 'white' }}>
                    Day {day.day_number}
                  </h3>
                  <span style={{ fontSize: '0.78rem', color: 'rgba(255,255,255,0.5)' }}>{day.date}</span>
                </div>
              </div>
              {day.summary && (
                <p style={{ margin: '0.625rem 0 0', fontSize: '0.875rem', color: 'rgba(255,255,255,0.65)', lineHeight: 1.4, maxWidth: '600px' }}>
                  {day.summary}
                </p>
              )}
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexShrink: 0 }}>
              <span style={{ fontSize: '0.78rem', color: 'rgba(255,255,255,0.45)' }}>
                {totalAttractions} place{totalAttractions !== 1 ? 's' : ''}
              </span>
              <motion.div animate={{ rotate: isOpen ? 180 : 0 }} transition={{ duration: 0.2 }}>
                <ChevronDown size={18} color="rgba(255,255,255,0.5)" />
              </motion.div>
            </div>
          </div>
        </div>
      </button>

      {/* Collapsible body */}
      <AnimatePresence initial={false}>
        {isOpen && (
          <motion.div
            key="body"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: 'easeInOut' }}
            style={{ overflow: 'hidden' }}
          >
            <div style={{ padding: '1.25rem 1.5rem' }}>
              <DaySection label="Morning" icon={<Sun size={14} />} items={day.morning} color="#fbbf24" />
              <DaySection label="Afternoon" icon={<Sunset size={14} />} items={day.afternoon} color="#f97316" />
              <DaySection label="Evening" icon={<Moon size={14} />} items={day.evening} color="#818cf8" />

              {/* Meal suggestions */}
              {(day.lunch_suggestion || day.dinner_suggestion) && (
                <div style={{
                  marginTop: '1rem',
                  padding: '1rem',
                  background: 'rgba(139,92,246,0.08)',
                  borderRadius: '0.75rem',
                  border: '1px solid rgba(139,92,246,0.15)',
                }}>
                  <div style={{ fontWeight: 600, fontSize: '0.8rem', color: '#c084fc', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
                    <Utensils size={13} /> Dining
                  </div>
                  {day.lunch_suggestion && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.4rem' }}>
                      <Coffee size={13} color="rgba(255,255,255,0.4)" />
                      <span style={{ fontSize: '0.83rem', color: 'rgba(255,255,255,0.65)' }}>
                        <strong style={{ color: 'rgba(255,255,255,0.8)' }}>Lunch:</strong> {day.lunch_suggestion}
                      </span>
                    </div>
                  )}
                  {day.dinner_suggestion && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <Utensils size={13} color="rgba(255,255,255,0.4)" />
                      <span style={{ fontSize: '0.83rem', color: 'rgba(255,255,255,0.65)' }}>
                        <strong style={{ color: 'rgba(255,255,255,0.8)' }}>Dinner:</strong> {day.dinner_suggestion}
                      </span>
                    </div>
                  )}
                </div>
              )}

              {/* Transportation suggestion & travel/walking times summary */}
              {(day.transportation || day.estimated_travel_time_minutes > 0 || (day.estimated_walking_time_minutes && day.estimated_walking_time_minutes > 0)) && (
                <div style={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  gap: '1rem',
                  marginTop: '1rem',
                  padding: '0.75rem 1rem',
                  background: 'rgba(255,255,255,0.02)',
                  border: '1px solid rgba(255,255,255,0.05)',
                  borderRadius: '0.75rem',
                }}>
                  {day.transportation && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem', fontSize: '0.8rem', color: 'rgba(255,255,255,0.6)' }}>
                      <strong>🚊 Transport Suggestion:</strong> {day.transportation}
                    </div>
                  )}
                  {day.estimated_travel_time_minutes > 0 && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem', fontSize: '0.8rem', color: 'rgba(255,255,255,0.6)' }}>
                      <strong>⏱️ Travel Time:</strong> {day.estimated_travel_time_minutes} min
                    </div>
                  )}
                  {day.estimated_walking_time_minutes && day.estimated_walking_time_minutes > 0 ? (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem', fontSize: '0.8rem', color: 'rgba(255,255,255,0.6)' }}>
                      <strong>🚶 Walking Time:</strong> {day.estimated_walking_time_minutes} min
                    </div>
                  ) : null}
                </div>
              )}

              {/* Daily budget breakdown */}
              {day.daily_budget && (
                <div style={{
                  marginTop: '1rem',
                  padding: '1rem',
                  background: 'rgba(16,185,129,0.04)',
                  border: '1px solid rgba(16,185,129,0.1)',
                  borderRadius: '0.75rem',
                }}>
                  <div style={{ fontWeight: 600, fontSize: '0.8rem', color: '#34d399', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '0.5rem' }}>
                    💰 Estimated Daily Budget
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(100px, 1fr))', gap: '0.5rem', fontSize: '0.8rem' }}>
                    <div>
                      <span style={{ color: 'rgba(255,255,255,0.4)' }}>Food:</span>{' '}
                      <span style={{ color: 'rgba(255,255,255,0.8)', fontWeight: 600 }}>₹{day.daily_budget.food.toLocaleString('en-IN')}</span>
                    </div>
                    <div>
                      <span style={{ color: 'rgba(255,255,255,0.4)' }}>Transport:</span>{' '}
                      <span style={{ color: 'rgba(255,255,255,0.8)', fontWeight: 600 }}>₹{day.daily_budget.transport.toLocaleString('en-IN')}</span>
                    </div>
                    <div>
                      <span style={{ color: 'rgba(255,255,255,0.4)' }}>Tickets:</span>{' '}
                      <span style={{ color: 'rgba(255,255,255,0.8)', fontWeight: 600 }}>₹{day.daily_budget.tickets.toLocaleString('en-IN')}</span>
                    </div>
                    <div>
                      <span style={{ color: '#34d399', fontWeight: 600 }}>Daily Cost:</span>{' '}
                      <span style={{ color: '#34d399', fontWeight: 800 }}>₹{day.daily_budget.total.toLocaleString('en-IN')}</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Daily travel tip */}
              {day.travel_tip && (
                <div style={{
                  marginTop: '1rem',
                  padding: '0.75rem 1rem',
                  background: 'rgba(245,158,11,0.06)',
                  border: '1px solid rgba(245,158,11,0.15)',
                  borderRadius: '0.75rem',
                  fontSize: '0.8rem',
                  color: 'rgba(255,255,255,0.7)',
                  lineHeight: 1.5
                }}>
                  <strong style={{ color: '#fbbf24' }}>💡 Travel Tip:</strong> {day.travel_tip}
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
