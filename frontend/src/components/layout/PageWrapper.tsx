import { motion } from 'framer-motion'
import { Navbar } from './Navbar'

interface PageWrapperProps {
  children: React.ReactNode
  className?: string
}

export function PageWrapper({ children, className = '' }: PageWrapperProps) {
  return (
    <div style={{ minHeight: '100vh', background: '#0f0a1e' }}>
      <Navbar />
      <motion.main
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: 'easeOut' }}
        style={{ paddingTop: '64px' }}
        className={className}
      >
        {children}
      </motion.main>
    </div>
  )
}
