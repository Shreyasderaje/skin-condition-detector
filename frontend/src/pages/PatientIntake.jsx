import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { toast } from 'react-toastify'
import api, { apiError } from '../services/api'

const TALUKAS = [
  'Mulki', 'Surathkal', 'Mangaluru', 'Bantwal', 'Puttur', 'Sullia',
  'Belthangady', 'Moodabidri', 'Karkala', 'Udupi', 'Kundapura', 'Brahmavar',
]

// Offline fallback: the in-progress intake is kept in localStorage so a
// dropped rural connection doesn't lose the form (see 3.2 in the spec).
const DRAFT_KEY = 'skinscreen:intake-draft'

const draftOrDefault = () => {
  try {
    return (
      JSON.parse(localStorage.getItem(DRAFT_KEY) || 'null') || {
        age: '',
        gender: '',
        location: '',
        contact_number: '',
        consent_to_screening: false,
        consent_to_data_storage: false,
      }
    )
  } catch {
    return {
      age: '',
      gender: '',
      location: '',
      contact_number: '',
      consent_to_screening: false,
      consent_to_data_storage: false,
    }
  }
}

export default function PatientIntake() {
  const navigate = useNavigate()
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm({ defaultValues: draftOrDefault() })

  useEffect(() => {
    const subscription = watch((values) => {
      try {
        localStorage.setItem(DRAFT_KEY, JSON.stringify(values))
      } catch {
        /* storage full or unavailable - draft persistence is best-effort */
      }
    })
    return () => subscription.unsubscribe()
  }, [watch])

  const onSubmit = async (data) => {
    try {
      const { data: patient } = await api.post('/patients', {
        age: Number(data.age),
        gender: data.gender,
        location: data.location,
        contact_number: data.contact_number || undefined,
      })
      await api.post('/consent', {
        patient_id: patient.patient_id,
        consent_to_screening: true,
        consent_to_data_storage: !!data.consent_to_data_storage,
      })
      localStorage.removeItem(DRAFT_KEY)
      toast.success(`Patient registered (ID: ${patient.patient_id})`)
      navigate(`/upload/${patient.patient_id}`)
    } catch (error) {
      toast.error(apiError(error))
    }
  }

  return (
    <div className="mx-auto max-w-xl">
      <div className="card">
        <h1 className="text-2xl font-bold">Patient Intake</h1>
        <p className="mt-1 text-sm text-slate-500">
          Register the patient, then upload the skin image for screening.
        </p>

        <form onSubmit={handleSubmit(onSubmit)} className="mt-5 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label" htmlFor="age">Age</label>
              <input
                id="age"
                type="number"
                className="input"
                {...register('age', { required: 'Age is required', min: 1, max: 120 })}
              />
              {errors.age && <p className="mt-1 text-xs text-red-600">{errors.age.message}</p>}
            </div>
            <div>
              <label className="label" htmlFor="gender">Gender</label>
              <select id="gender" className="input" {...register('gender', { required: 'Gender is required' })}>
                <option value="">Select…</option>
                <option>Male</option>
                <option>Female</option>
                <option>Other</option>
              </select>
              {errors.gender && <p className="mt-1 text-xs text-red-600">{errors.gender.message}</p>}
            </div>
          </div>

          <div>
            <label className="label" htmlFor="location">Location / Taluka</label>
            <select id="location" className="input" {...register('location', { required: 'Location is required' })}>
              <option value="">Select taluka…</option>
              {TALUKAS.map((t) => <option key={t}>{t}</option>)}
            </select>
            {errors.location && <p className="mt-1 text-xs text-red-600">{errors.location.message}</p>}
          </div>

          <div>
            <label className="label" htmlFor="contact_number">Contact number (optional)</label>
            <input
              id="contact_number"
              className="input"
              placeholder="+919876543210"
              {...register('contact_number', {
                pattern: { value: /^\+?[0-9]{8,15}$/, message: 'Use E.164 format, e.g. +919876543210' },
              })}
            />
            {errors.contact_number && (
              <p className="mt-1 text-xs text-red-600">{errors.contact_number.message}</p>
            )}
          </div>

          <div className="space-y-2 rounded-xl bg-slate-50 p-4">
            <p className="text-sm font-semibold text-slate-700">Patient consent</p>
            <label className="flex items-start gap-2 text-sm">
              <input
                type="checkbox"
                className="mt-0.5 h-5 w-5"
                {...register('consent_to_screening', { required: 'Screening consent is required' })}
              />
              <span>
                Patient consents to AI skin screening and understands it is not a diagnosis.
              </span>
            </label>
            {errors.consent_to_screening && (
              <p className="text-xs text-red-600">{errors.consent_to_screening.message}</p>
            )}
            <label className="flex items-start gap-2 text-sm">
              <input type="checkbox" className="mt-0.5 h-5 w-5" {...register('consent_to_data_storage')} />
              <span>Patient consents to secure data storage for follow-up.</span>
            </label>
          </div>

          <button type="submit" className="btn-primary w-full" disabled={isSubmitting}>
            {isSubmitting ? 'Saving…' : 'Next: Upload Image →'}
          </button>
          <p className="text-center text-xs text-slate-400">
            Draft is saved on this device, so the form survives connection drops.
          </p>
        </form>
      </div>
    </div>
  )
}
