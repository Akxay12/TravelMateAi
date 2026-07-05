import React, { createContext, useContext, useState } from 'react'

// ── Types ─────────────────────────────────────────────

export type TravelStyle = 'budget' | 'standard' | 'luxury'

export interface TripDetails {
  destination: string
  start_date: string
  end_date: string
  budget: number
  travelers: number
  travel_style: TravelStyle
  places_per_day: number
  trip_days: number
  interests?: string
}

export interface AttractionItem {
  id: string
  name: string
  category: string
  description: string
  distance_km: number
  estimated_duration_minutes: number
  osm_tags: Record<string, string>
  quality_score?: number
  interest_score?: number
  final_score?: number
}

export interface TimeSlotItem {
  attraction_id: string
  name: string
  suggested_time: string
  duration_minutes: number
  notes: string
}

export interface DailyBudget {
  food: number
  transport: number
  tickets: number
  total: number
}

export interface DayPlan {
  day_number: number
  date: string
  summary: string
  morning: TimeSlotItem[]
  afternoon: TimeSlotItem[]
  evening: TimeSlotItem[]
  lunch_suggestion: string
  dinner_suggestion: string
  estimated_travel_time_minutes: number
  estimated_walking_time_minutes?: number
  transportation?: string | null
  daily_budget?: DailyBudget | null
  travel_tip?: string | null
  notes?: string | null
}

export interface BudgetSummary {
  accommodation: number
  food: number
  transport: number
  tickets: number
  miscellaneous: number
  total: number
  remaining: number
  status: string
}

export interface WeatherSummary {
  condition: string
  temperature_range: string
  rain_probability: string
  wind_speed: string
  humidity: string
  risk_level: string
  advisories?: string[]
  packing_checklist?: string[]
}

export interface Itinerary {
  destination: string
  total_days: number
  days: DayPlan[]
  trip_title?: string | null
  overview?: string | null
  final_summary?: string | null
  budget_notes?: string | null
  weather_notes?: string | null
  packing_reminder?: string | null
  budget_summary?: BudgetSummary | null
  weather_summary?: WeatherSummary | null
  important_travel_advice?: string[]
  emergency_tips?: string[]
}

// ── Context ───────────────────────────────────────────

interface TripContextValue {
  tripDetails: TripDetails | null
  attractions: AttractionItem[]
  selectedIds: Set<string>
  itinerary: Itinerary | null

  setTripDetails: (details: TripDetails) => void
  setAttractions: (attractions: AttractionItem[]) => void
  toggleAttraction: (id: string) => void
  clearSelection: () => void
  setItinerary: (itinerary: Itinerary) => void
  resetAll: () => void
}

const TripContext = createContext<TripContextValue | null>(null)

// ── Provider ──────────────────────────────────────────

export function TripProvider({ children }: { children: React.ReactNode }) {
  const [tripDetails, setTripDetailsState] = useState<TripDetails | null>(null)
  const [attractions, setAttractionsState] = useState<AttractionItem[]>([])
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [itinerary, setItineraryState] = useState<Itinerary | null>(null)

  const setTripDetails = (details: TripDetails) => {
    setTripDetailsState(details)
  }

  const setAttractions = (items: AttractionItem[]) => {
    setAttractionsState(items)
    setSelectedIds(new Set())
  }

  const toggleAttraction = (id: string) => {
    setSelectedIds(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const clearSelection = () => setSelectedIds(new Set())

  const setItinerary = (data: Itinerary) => setItineraryState(data)

  const resetAll = () => {
    setTripDetailsState(null)
    setAttractionsState([])
    setSelectedIds(new Set())
    setItineraryState(null)
  }

  return (
    <TripContext.Provider value={{
      tripDetails, attractions, selectedIds, itinerary,
      setTripDetails, setAttractions, toggleAttraction,
      clearSelection, setItinerary, resetAll,
    }}>
      {children}
    </TripContext.Provider>
  )
}

// ── Hook ──────────────────────────────────────────────

export function useTripContext(): TripContextValue {
  const ctx = useContext(TripContext)
  if (!ctx) throw new Error('useTripContext must be used within TripProvider')
  return ctx
}
