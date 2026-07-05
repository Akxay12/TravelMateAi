import { Link, useLocation } from 'react-router-dom'
import { MapPin, Compass } from 'lucide-react'
import { useTripContext } from '../../contexts/TripContext'

const steps = [
  { path: '/', label: 'Home' },
  { path: '/plan', label: 'Trip Details' },
  { path: '/attractions', label: 'Attractions' },
  { path: '/itinerary', label: 'Itinerary' },
]

export function Navbar() {
  const location = useLocation()
  const { resetAll } = useTripContext()
  const isHome = location.pathname === '/'

  return (
    <nav style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      zIndex: 50,
      background: 'rgba(15, 10, 30, 0.8)',
      backdropFilter: 'blur(20px)',
      borderBottom: '1px solid rgba(255,255,255,0.08)',
    }}>
      <div style={{ maxWidth: '1280px', margin: '0 auto', padding: '0 1.5rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', height: '64px' }}>
        {/* Logo */}
        <Link to="/" onClick={resetAll} style={{ display: 'flex', alignItems: 'center', gap: '0.625rem', textDecoration: 'none' }}>
          <div style={{
            width: '36px', height: '36px', borderRadius: '10px',
            background: 'linear-gradient(135deg, #7c3aed, #4f46e5)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 4px 12px rgba(124,58,237,0.4)',
          }}>
            <Compass size={20} color="white" />
          </div>
          <span style={{ fontFamily: 'Outfit, sans-serif', fontWeight: 700, fontSize: '1.25rem', color: 'white' }}>
            TravelMate <span style={{ color: '#a855f7' }}>AI</span>
          </span>
        </Link>

        {/* Step indicators (hide on home) */}
        {!isHome && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            {steps.slice(1).map((step, i) => {
              const isActive = location.pathname === step.path
              const stepIndex = steps.findIndex(s => s.path === location.pathname)
              const isPast = i < stepIndex - 1
              return (
                <div key={step.path} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <div style={{
                    display: 'flex', alignItems: 'center', gap: '0.375rem',
                    padding: '0.375rem 0.75rem',
                    borderRadius: '9999px',
                    fontSize: '0.8rem', fontWeight: 500,
                    background: isActive ? 'rgba(139,92,246,0.25)' : isPast ? 'rgba(255,255,255,0.05)' : 'transparent',
                    color: isActive ? '#c084fc' : isPast ? 'rgba(255,255,255,0.5)' : 'rgba(255,255,255,0.3)',
                    border: isActive ? '1px solid rgba(139,92,246,0.4)' : '1px solid transparent',
                  }}>
                    <span style={{
                      width: '18px', height: '18px',
                      borderRadius: '50%',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: '0.7rem', fontWeight: 700,
                      background: isActive ? '#7c3aed' : isPast ? 'rgba(255,255,255,0.15)' : 'rgba(255,255,255,0.08)',
                      color: 'white',
                    }}>{i + 1}</span>
                    <span className="hidden sm:inline">{step.label}</span>
                  </div>
                  {i < 2 && <div style={{ width: '20px', height: '1px', background: 'rgba(255,255,255,0.1)' }} />}
                </div>
              )
            })}
          </div>
        )}

        {/* CTA */}
        {isHome && (
          <Link to="/plan" className="btn-primary" style={{ padding: '0.5rem 1.25rem', fontSize: '0.875rem' }}>
            <MapPin size={15} /> Plan a Trip
          </Link>
        )}
      </div>
    </nav>
  )
}
