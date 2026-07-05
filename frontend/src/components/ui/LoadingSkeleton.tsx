// Generic loading skeleton block
interface SkeletonProps {
  width?: string
  height?: string
  className?: string
  style?: React.CSSProperties
}

export function Skeleton({ width = '100%', height = '1rem', style }: SkeletonProps) {
  return (
    <div
      className="skeleton"
      style={{ width, height, ...style }}
    />
  )
}

export function AttractionCardSkeleton() {
  return (
    <div style={{
      borderRadius: '1rem',
      overflow: 'hidden',
      background: 'rgba(255,255,255,0.04)',
      border: '1px solid rgba(255,255,255,0.06)',
    }}>
      <Skeleton height="180px" style={{ borderRadius: 0 }} />
      <div style={{ padding: '1rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        <Skeleton width="60%" height="0.875rem" />
        <Skeleton width="85%" height="1.125rem" />
        <Skeleton height="0.75rem" />
        <Skeleton width="70%" height="0.75rem" />
        <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.25rem' }}>
          <Skeleton width="80px" height="1.5rem" style={{ borderRadius: '9999px' }} />
          <Skeleton width="60px" height="1.5rem" style={{ borderRadius: '9999px' }} />
        </div>
      </div>
    </div>
  )
}
