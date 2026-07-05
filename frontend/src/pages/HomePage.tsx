import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ArrowRight, MapPin, Sparkles, Route, CheckSquare } from 'lucide-react'
import { Navbar } from '../components/layout/Navbar'

const features = [
  {
    icon: <MapPin size={22} />,
    title: 'Real Attractions',
    desc: 'We fetch verified places from OpenStreetMap — no fake or invented destinations.',
    color: '#a855f7',
  },
  {
    icon: <CheckSquare size={22} />,
    title: 'You Choose',
    desc: 'Browse all available attractions and hand-pick exactly what interests you.',
    color: '#818cf8',
  },
  {
    icon: <Sparkles size={22} />,
    title: 'AI Organizes',
    desc: 'Gemini arranges your selections into an optimized, day-by-day itinerary.',
    color: '#60a5fa',
  },
]

export function HomePage() {
  return (
    <div style={{ minHeight: '100vh', background: '#0f0a1e' }}>
      <Navbar />

      {/* Hero */}
      <section className="hero-bg" style={{ position: 'relative', overflow: 'hidden', paddingTop: '120px', paddingBottom: '100px' }}>
        {/* Floating orbs */}
        <div className="orb orb-purple" style={{ width: '500px', height: '500px', top: '-100px', left: '50%', transform: 'translateX(-30%)' }} />
        <div className="orb orb-indigo" style={{ width: '300px', height: '300px', bottom: '0', left: '10%' }} />

        <div style={{ maxWidth: '900px', margin: '0 auto', padding: '0 1.5rem', textAlign: 'center', position: 'relative', zIndex: 1 }}>
          {/* Badge */}
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            style={{
              display: 'inline-flex', alignItems: 'center', gap: '0.5rem',
              padding: '0.375rem 1rem', borderRadius: '9999px',
              background: 'rgba(139,92,246,0.15)', border: '1px solid rgba(139,92,246,0.3)',
              marginBottom: '2rem',
            }}
          >
            <Sparkles size={14} color="#c084fc" />
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#c084fc' }}>Powered by Gemini AI + OpenStreetMap</span>
          </motion.div>

          {/* Headline */}
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            style={{
              fontFamily: 'Outfit, sans-serif',
              fontSize: 'clamp(2.5rem, 6vw, 4.5rem)',
              fontWeight: 900,
              lineHeight: 1.1,
              color: 'white',
              margin: '0 0 1.5rem',
              letterSpacing: '-0.02em',
            }}
          >
            Your Trip, Your Picks,{' '}
            <span className="gradient-text">AI-Organized</span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            style={{
              fontSize: 'clamp(1rem, 2vw, 1.25rem)',
              color: 'rgba(255,255,255,0.65)',
              maxWidth: '600px', margin: '0 auto 2.5rem',
              lineHeight: 1.7,
            }}
          >
            Browse real attractions from OpenStreetMap, select what excites you,
            and let Gemini build the perfect day-by-day itinerary from your choices.
          </motion.p>

          {/* CTA buttons */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap' }}
          >
            <Link to="/plan" className="btn-primary" id="hero-cta-plan" style={{ fontSize: '1.05rem', padding: '1rem 2.25rem' }}>
              Start Planning <ArrowRight size={18} />
            </Link>
            <a href="#how-it-works" className="btn-secondary" style={{ fontSize: '1.05rem', padding: '1rem 2.25rem' }}>
              How it works
            </a>
          </motion.div>

          {/* Stats */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.5 }}
            style={{ display: 'flex', gap: '2.5rem', justifyContent: 'center', marginTop: '4rem', flexWrap: 'wrap' }}
          >
            {[['100%', 'Real Destinations'], ['0', 'Fake Places'], ['AI', 'Organized Plan']].map(([val, label]) => (
              <div key={label} style={{ textAlign: 'center' }}>
                <div style={{ fontFamily: 'Outfit, sans-serif', fontSize: '1.75rem', fontWeight: 800, color: 'white' }}>{val}</div>
                <div style={{ fontSize: '0.78rem', color: 'rgba(255,255,255,0.45)', marginTop: '0.25rem' }}>{label}</div>
              </div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* How it works */}
      <section id="how-it-works" style={{ padding: '6rem 1.5rem', maxWidth: '1100px', margin: '0 auto' }}>
        <div style={{ textAlign: 'center', marginBottom: '3.5rem' }}>
          <h2 style={{ fontFamily: 'Outfit, sans-serif', fontSize: 'clamp(1.75rem, 3vw, 2.5rem)', fontWeight: 800, color: 'white', margin: '0 0 1rem' }}>
            How It <span className="gradient-text">Works</span>
          </h2>
          <p style={{ color: 'rgba(255,255,255,0.5)', fontSize: '1rem', maxWidth: '500px', margin: '0 auto' }}>
            Three simple steps to a perfectly organized trip
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.5rem' }}>
          {features.map((feature, i) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4, delay: i * 0.12 }}
              className="glass"
              style={{ padding: '2rem', position: 'relative', overflow: 'hidden' }}
            >
              <div style={{
                position: 'absolute', top: 0, left: 0, right: 0, height: '3px',
                background: `linear-gradient(90deg, ${feature.color}, transparent)`,
              }} />
              <div style={{
                width: '48px', height: '48px', borderRadius: '12px',
                background: `${feature.color}20`,
                border: `1px solid ${feature.color}30`,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                marginBottom: '1.25rem', color: feature.color,
              }}>
                {feature.icon}
              </div>
              <div style={{
                position: 'absolute', top: '1.5rem', right: '1.5rem',
                fontFamily: 'Outfit, sans-serif', fontSize: '3rem', fontWeight: 900,
                color: 'rgba(255,255,255,0.04)',
              }}>{i + 1}</div>
              <h3 style={{ margin: '0 0 0.625rem', fontWeight: 700, fontSize: '1.1rem', color: 'white' }}>{feature.title}</h3>
              <p style={{ margin: 0, color: 'rgba(255,255,255,0.55)', fontSize: '0.9rem', lineHeight: 1.6 }}>{feature.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Bottom CTA */}
      <section style={{
        margin: '0 1.5rem 6rem',
        maxWidth: '700px',
        marginLeft: 'auto', marginRight: 'auto',
        padding: '3.5rem',
        background: 'linear-gradient(135deg, rgba(124,58,237,0.2), rgba(79,70,229,0.15))',
        border: '1px solid rgba(139,92,246,0.25)',
        borderRadius: '1.5rem',
        textAlign: 'center',
        position: 'relative', overflow: 'hidden',
      }}>
        <Route size={40} color="rgba(168,85,247,0.5)" style={{ marginBottom: '1rem' }} />
        <h2 style={{ fontFamily: 'Outfit, sans-serif', fontWeight: 800, fontSize: '1.75rem', color: 'white', margin: '0 0 0.75rem' }}>
          Ready to explore?
        </h2>
        <p style={{ color: 'rgba(255,255,255,0.55)', marginBottom: '2rem', fontSize: '0.95rem' }}>
          Enter your destination and travel dates to get started.
        </p>
        <Link to="/plan" className="btn-primary" id="bottom-cta-plan">
          Plan My Trip <ArrowRight size={16} />
        </Link>
      </section>
    </div>
  )
}
