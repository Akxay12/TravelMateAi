import type { AttractionItem } from '../../contexts/TripContext'
import { AttractionCard } from './AttractionCard'
import { AttractionCardSkeleton } from '../ui/LoadingSkeleton'

interface AttractionGridProps {
  attractions: AttractionItem[]
  selectedIds: Set<string>
  onToggle: (id: string) => void
  isLoading?: boolean
}

export function AttractionGrid({ attractions, selectedIds, onToggle, isLoading }: AttractionGridProps) {
  const gridStyle: React.CSSProperties = {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
    gap: '1.25rem',
  }

  if (isLoading) {
    return (
      <div style={gridStyle}>
        {Array.from({ length: 12 }).map((_, i) => (
          <AttractionCardSkeleton key={i} />
        ))}
      </div>
    )
  }

  return (
    <div style={gridStyle}>
      {attractions.map((attraction, i) => (
        <AttractionCard
          key={attraction.id}
          attraction={attraction}
          isSelected={selectedIds.has(attraction.id)}
          onToggle={onToggle}
          index={i}
        />
      ))}
    </div>
  )
}
