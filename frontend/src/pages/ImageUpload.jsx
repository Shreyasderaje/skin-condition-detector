import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { toast } from 'react-toastify'
import DisclaimerBanner from '../components/DisclaimerBanner'
import api, { apiError } from '../services/api'

export default function ImageUpload() {
  const { patientId } = useParams()
  const navigate = useNavigate()
  const [patient, setPatient] = useState(null)
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [temperature, setTemperature] = useState('')
  const [uploading, setUploading] = useState(false)
  const [dragOver, setDragOver] = useState(false)
  const inputRef = useRef(null)

  useEffect(() => {
    api
      .get(`/patients/${patientId}`)
      .then((r) => setPatient(r.data))
      .catch((e) => {
        toast.error(apiError(e))
        navigate('/intake')
      })
  }, [patientId, navigate])

  useEffect(
    () => () => {
      if (preview) URL.revokeObjectURL(preview)
    },
    [preview],
  )

  const pickFile = (f) => {
    if (!f) return
    if (!/^image\/(jpe?g|png)$/.test(f.type)) {
      toast.error('Use a JPG or PNG image')
      return
    }
    if (f.size > 5 * 1024 * 1024) {
      toast.error('Image must be under 5MB')
      return
    }
    setFile(f)
    setPreview(URL.createObjectURL(f))
  }

  const startScreening = async () => {
    if (!file) return
    setUploading(true)
    try {
      const form = new FormData()
      form.append('image', file)
      form.append('patient_id', patientId)
      if (temperature) form.append('vitals_temp', temperature)
      const { data } = await api.post('/consultations/upload', form)
      toast.success('Screening complete')
      navigate(`/results/${data.consultation_id}`)
    } catch (error) {
      toast.error(apiError(error))
      setUploading(false)
    }
  }

  return (
    <div className="mx-auto max-w-2xl space-y-5">
      <DisclaimerBanner />

      <div className="card">
        <h1 className="text-2xl font-bold">Upload Skin Image</h1>
        {patient && (
          <p className="mt-1 text-sm text-slate-500">
            Patient #{patient.patient_id} · {patient.age}y {patient.gender} · {patient.location}
          </p>
        )}

        <div
          role="button"
          tabIndex={0}
          onClick={() => inputRef.current?.click()}
          onKeyDown={(e) => e.key === 'Enter' && inputRef.current?.click()}
          onDragOver={(e) => {
            e.preventDefault()
            setDragOver(true)
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => {
            e.preventDefault()
            setDragOver(false)
            pickFile(e.dataTransfer.files?.[0])
          }}
          className={`mt-5 flex min-h-[220px] cursor-pointer flex-col items-center justify-center
            rounded-2xl border-2 border-dashed p-6 text-center transition
            ${dragOver ? 'border-teal-500 bg-teal-50' : 'border-slate-300 bg-slate-50 hover:bg-slate-100'}`}
        >
          {preview ? (
            <img src={preview} alt="Selected skin lesion" className="max-h-64 rounded-xl shadow" />
          ) : (
            <>
              <span className="text-4xl">📷</span>
              <p className="mt-3 font-semibold text-slate-700">
                Drag &amp; drop the skin photo here, or tap to browse
              </p>
              <p className="mt-1 text-xs text-slate-500">JPG or PNG · up to 5MB · well-lit, in focus</p>
            </>
          )}
          <input
            ref={inputRef}
            type="file"
            accept="image/jpeg,image/png"
            className="hidden"
            onChange={(e) => pickFile(e.target.files?.[0])}
          />
        </div>

        <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="label" htmlFor="temp">Temperature °C (optional)</label>
            <input
              id="temp"
              type="number"
              step="0.1"
              min="30"
              max="45"
              className="input"
              value={temperature}
              onChange={(e) => setTemperature(e.target.value)}
              placeholder="e.g. 37.5"
            />
          </div>
        </div>

        <div className="mt-5 flex flex-col gap-3 sm:flex-row">
          <button className="btn-primary flex-1" disabled={!file || uploading} onClick={startScreening}>
            {uploading ? 'Analyzing…' : 'Start Screening'}
          </button>
          <button className="btn-secondary" onClick={() => navigate('/intake')}>
            New Patient
          </button>
        </div>
      </div>

      {uploading && (
        <div className="card flex items-center gap-4 border-teal-300 bg-teal-50" role="status">
          <span className="h-6 w-6 animate-spin rounded-full border-4 border-teal-600 border-t-transparent" />
          <div>
            <p className="font-semibold text-teal-900">Analyzing image… 3–5 seconds</p>
            <p className="text-sm text-teal-800">Running the AI model on the uploaded photo.</p>
          </div>
        </div>
      )}
    </div>
  )
}
