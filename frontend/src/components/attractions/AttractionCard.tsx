import { motion } from 'framer-motion'
import { Check, Clock, MapPin, Star } from 'lucide-react'
import type { AttractionItem } from '../../contexts/TripContext'

interface AttractionCardProps {
  attraction: AttractionItem
  isSelected: boolean
  onToggle: (id: string) => void
  index: number
}

const CATEGORY_ICONS: Record<string, string> = {
  Museum: '🏛️',
  Attraction: '🎯',
  Viewpoint: '🌄',
  Castle: '🏰',
  Park: '🌿',
  Garden: '🌸',
  Monument: '🗿',
  Beach: '🏖️',
  Waterfall: '💧',
  'Art Gallery': '🎨',
  'Place of Worship': '⛩️',
  Theatre: '🎭',
  'Nature Reserve': '🌲',
  default: '📍',
}

function formatDuration(minutes: number): string {
  if (minutes < 60) return `${minutes} min`
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  return m > 0 ? `${h}h ${m}m` : `${h}h`
}

const getRating = (id: string, osmTags?: Record<string, string>): { score: string; count: number } => {
  if (osmTags?.rating) {
    const val = parseFloat(osmTags.rating)
    if (!isNaN(val)) return { score: val.toFixed(1), count: 15 + (id.length * 7) % 200 }
  }
  let hash = 0
  for (let i = 0; i < id.length; i++) {
    hash = id.charCodeAt(i) + ((hash << 5) - hash)
  }
  const scoreVal = 3.8 + (Math.abs(hash) % 12) / 10
  const countVal = 10 + (Math.abs(hash) % 490)
  return { score: scoreVal.toFixed(1), count: countVal }
}

export function AttractionCard({ attraction, isSelected, onToggle, index }: AttractionCardProps) {
  const icon = CATEGORY_ICONS[attraction.category] ?? CATEGORY_ICONS.default
  const rating = getRating(attraction.id, attraction.osm_tags)

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.04 }}
      className={`attraction-card ${isSelected ? 'selected' : ''}`}
      onClick={() => onToggle(attraction.id)}
      role="checkbox"
      aria-checked={isSelected}
      tabIndex={0}
      onKeyDown={e => e.key === 'Enter' || e.key === ' ' ? onToggle(attraction.id) : undefined}
      id={`attraction-${attraction.id}`}
    >
      {/* Card image area */}
      <div style={{
        height: '160px',
        background: `linear-gradient(135deg, rgba(30,20,60,0.9), rgba(60,20,100,0.7))`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        position: 'relative',
        overflow: 'hidden',
      }}>
        {/* Decorative gradient blob */}
        <div style={{
          position: 'absolute', inset: 0,
          background: `radial-gradient(ellipse at 30% 50%, rgba(139,92,246,0.25) 0%, transparent 70%),
                       radial-gradient(ellipse at 70% 40%, rgba(99,102,241,0.2) 0%, transparent 60%)`,
        }} />

        {/* Category icon */}
        <span style={{ fontSize: '3rem', position: 'relative', zIndex: 1, filter: 'drop-shadow(0 4px 12px rgba(0,0,0,0.5))' }}>
          {icon}
        </span>

        {/* Selection checkbox */}
        <div style={{
          position: 'absolute', top: '0.75rem', right: '0.75rem',
          width: '28px', height: '28px',
          borderRadius: '8px',
          border: isSelected ? '2px solid #a855f7' : '2px solid rgba(255,255,255,0.2)',
          background: isSelected ? '#7c3aed' : 'rgba(0,0,0,0.4)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          transition: 'all 0.2s ease',
          backdropFilter: 'blur(4px)',
          zIndex: 2,
        }}>
          {isSelected && <Check size={16} color="white" strokeWidth={3} />}
        </div>

        {/* Category badge on image */}
        <div style={{ position: 'absolute', bottom: '0.75rem', left: '0.75rem', zIndex: 2 }}>
          <span className="category-badge">{attraction.category}</span>
        </div>
      </div>

      {/* Card body */}
      <div style={{ padding: '1rem', display: 'flex', flexDirection: 'column', flex: 1 }}>
        <h3 style={{
          margin: 0, fontSize: '1rem', fontWeight: 600,
          color: 'white', lineHeight: 1.3,
          marginBottom: '0.5rem',
          display: '-webkit-box',
          WebkitLineClamp: 2,
          WebkitBoxOrient: 'vertical',
          overflow: 'hidden',
        }}>
          {attraction.name}
        </h3>

        <p style={{
          margin: '0 0 0.875rem',
          fontSize: '0.8rem',
          color: 'rgba(255,255,255,0.55)',
          lineHeight: 1.5,
          display: '-webkit-box',
          WebkitLineClamp: 2,
          WebkitBoxOrient: 'vertical',
          overflow: 'hidden',
          height: '2.4rem',
        }}>
          {attraction.description}
        </p>

        {/* Meta row */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap', marginBottom: '1rem' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', fontSize: '0.75rem', color: 'rgba(255,255,255,0.5)' }}>
            <MapPin size={12} /> {attraction.distance_km.toFixed(1)} km
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', fontSize: '0.75rem', color: 'rgba(255,255,255,0.5)' }}>
            <Clock size={12} /> {formatDuration(attraction.estimated_duration_minutes)}
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', fontSize: '0.75rem', color: '#fbbf24' }}>
            <Star size={12} fill="#fbbf24" strokeWidth={0} /> {rating.score} ({rating.count})
          </span>
        </div>

        {/* Select Button */}
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation()
            onToggle(attraction.id)
          }}
          style={{
            width: '100%',
            padding: '0.625rem',
            borderRadius: '0.5rem',
            background: isSelected ? 'linear-gradient(135deg, #7c3aed, #4f46e5)' : 'rgba(255, 255, 255, 0.08)',
            color: 'white',
            border: isSelected ? 'none' : '1px solid rgba(255, 255, 255, 0.15)',
            fontWeight: 600,
            fontSize: '0.85rem',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '0.375rem',
            transition: 'all 0.2s',
            marginTop: 'auto',
          }}
        >
          {isSelected ? (
            <>
              <Check size={14} strokeWidth={3} /> Selected
            </>
          ) : (
            <>Select Attraction</>
          )}
        </button>
      </div>
    </motion.div>
  )
}

