import type { AttractionItem, Itinerary, TravelStyle } from '../contexts/TripContext'

export interface ItineraryRequest {
  destination: string
  start_date: string
  end_date: string
  budget: number
  travelers: number
  travel_style: TravelStyle
  selected_attractions: AttractionItem[]
  places_per_day?: number  // forwarded to backend for max-attraction validation
}

export async function generateItinerary(request: ItineraryRequest): Promise<Itinerary> {
  // Strip only trip_days (frontend-only display field); places_per_day is forwarded to backend
  const { trip_days, ...apiDetails } = request as any
  const res = await fetch('/api/itinerary/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(apiDetails),
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Request failed' }))
    throw new Error(err.detail ?? 'Failed to generate itinerary')
  }

  return res.json()
}
