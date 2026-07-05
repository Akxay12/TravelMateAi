import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { TripProvider } from './contexts/TripContext'
import { HomePage } from './pages/HomePage'
import { TripFormPage } from './pages/TripFormPage'
import { AttractionsPage } from './pages/AttractionsPage'
import { ItineraryPage } from './pages/ItineraryPage'

export default function App() {
  return (
    <TripProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/plan" element={<TripFormPage />} />
          <Route path="/attractions" element={<AttractionsPage />} />
          <Route path="/itinerary" element={<ItineraryPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </TripProvider>
  )
}
