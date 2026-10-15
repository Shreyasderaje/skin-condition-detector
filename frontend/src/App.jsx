import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { ToastContainer } from 'react-toastify'
import Footer from './components/Footer'
import Header from './components/Header'
import RequireAuth from './components/RequireAuth'
import { AuthProvider } from './context/AuthContext'
import ConsultationHistory from './pages/ConsultationHistory'
import Dashboard from './pages/Dashboard'
import Disclaimer from './pages/Disclaimer'
import ImageUpload from './pages/ImageUpload'
import Login from './pages/Login'
import PatientIntake from './pages/PatientIntake'
import ReferralForm from './pages/ReferralForm'
import Results from './pages/Results'

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <div className="flex min-h-screen flex-col">
          <Header />
          <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6">
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/disclaimer" element={<Disclaimer />} />
              <Route element={<RequireAuth />}>
                <Route path="/" element={<Dashboard />} />
                <Route path="/intake" element={<PatientIntake />} />
                <Route path="/upload/:patientId" element={<ImageUpload />} />
                <Route path="/results/:consultationId" element={<Results />} />
                <Route path="/referral/:consultationId" element={<ReferralForm />} />
                <Route path="/history" element={<ConsultationHistory />} />
              </Route>
            </Routes>
          </main>
          <Footer />
          <ToastContainer position="top-center" autoClose={4000} newestOnTop />
        </div>
      </AuthProvider>
    </BrowserRouter>
  )
}
