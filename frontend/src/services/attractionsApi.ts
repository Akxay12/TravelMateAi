import type { AttractionItem, TripDetails } from '../contexts/TripContext'

export interface AttractionSearchResponse {
  destination: string
  coordinates: { lat: number; lon: number }
  attractions: AttractionItem[]
}

export async function searchAttractions(details: TripDetails): Promise<AttractionSearchResponse> {
  // Strip frontend-only fields to strictly preserve API contracts
  const { places_per_day, trip_days, ...apiDetails } = details
  const res = await fetch('/api/attractions/search', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(apiDetails),
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Request failed' }))
    throw new Error(err.detail ?? 'Failed to fetch attractions')
  }

  return res.json()
}
