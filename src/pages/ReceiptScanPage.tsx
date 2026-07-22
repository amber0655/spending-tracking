import { useEffect, useRef, useState, type ChangeEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { AppHeader } from '../components/AppShell'
import { Icon } from '../components/Icon'
import { scanReceipt, type ReceiptScanResult } from '../lib/receiptsApi'

type ScanStatus = 'choose' | 'scanning' | 'review' | 'error'

export function ReceiptScanPage() {
  const [status, setStatus] = useState<ScanStatus>('choose')
  const [imageUrl, setImageUrl] = useState('')
  const [fields, setFields] = useState<ReceiptScanResult | null>(null)
  const [error, setError] = useState('')
  const cameraInput = useRef<HTMLInputElement>(null)
  const galleryInput = useRef<HTMLInputElement>(null)
  const navigate = useNavigate()

  useEffect(() => () => {
    if (imageUrl) URL.revokeObjectURL(imageUrl)
  }, [imageUrl])

  async function scan(file: File) {
    if (!file.type.startsWith('image/')) {
      setError('Please choose an image file.')
      setStatus('error')
      return
    }
    if (file.size > 15 * 1024 * 1024) {
      setError('That image is larger than 15 MB. Please choose a smaller photo.')
      setStatus('error')
      return
    }

    if (imageUrl) URL.revokeObjectURL(imageUrl)
    setImageUrl(URL.createObjectURL(file))
    setStatus('scanning')
    setError('')

    try {
      setFields(await scanReceipt(file))
      setStatus('review')
    } catch (scanError) {
      console.error(scanError)
      setError(scanError instanceof Error ? scanError.message : 'We could not scan this receipt.')
      setStatus('error')
    }
  }

  function chooseImage(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (file) void scan(file)
  }

  function reset() {
    if (imageUrl) URL.revokeObjectURL(imageUrl)
    setImageUrl('')
    setFields(null)
    setError('')
    setStatus('choose')
  }

  function useResult() {
    if (!fields) return
    navigate('/expenses/new', {
      state: {
        receipt: {
          amount: fields.amount,
          merchant: fields.merchant,
          date: fields.date,
        },
      },
    })
  }

  return (
    <div className="scan-page">
      <AppHeader />
      <main className="scan-stage">
        <div className="scan-texture" />
        <div className="scan-content">
          <input ref={cameraInput} className="sr-only" type="file" accept="image/*" capture="environment" onChange={chooseImage} />
          <input ref={galleryInput} className="sr-only" type="file" accept="image/*" onChange={chooseImage} />

          {status === 'choose' && (
            <section className="scan-start" aria-labelledby="scan-title">
              <div className="scan-start-icon"><Icon name="scan" className="size-9" /></div>
              <h2 id="scan-title">Scan a receipt</h2>
              <p>Take a clear photo or upload one from your library. It will be sent securely for scanning.</p>
              <button className="scan-action-primary" onClick={() => cameraInput.current?.click()}>
                <Icon name="scan" className="size-5" /> Take a photo
              </button>
              <button className="scan-action-secondary" onClick={() => galleryInput.current?.click()}>
                <Icon name="gallery" className="size-5" /> Upload a receipt
              </button>
              <p className="scan-hint">For best results, flatten the receipt and avoid shadows.</p>
            </section>
          )}

          {(status === 'scanning' || status === 'review' || status === 'error') && (
            <section className="scan-preview" aria-live="polite">
              <div className="scan-image-shell">
                {imageUrl && <img src={imageUrl} alt="Selected receipt" />}
                {status === 'scanning' && <div className="scan-line" />}
              </div>

              {status === 'scanning' && (
                <div className="scan-processing">
                  <div className="flex items-center justify-center gap-2 text-[#6cf8bb]">
                    <Icon name="sparkles" className="size-5" />
                    <strong>Uploading and scanning receipt…</strong>
                  </div>
                  <div className="scan-progress"><span /></div>
                  <p>Please keep this page open while the server reads your receipt.</p>
                </div>
              )}

              {status === 'review' && fields && (
                <div className="scan-result">
                  <div className="flex items-center gap-2 text-[#6cf8bb]"><Icon name="check" className="size-5" /><strong>Receipt scanned</strong></div>
                  <label>Merchant<input value={fields.merchant} onChange={(event) => setFields({ ...fields, merchant: event.target.value })} placeholder="Merchant name" /></label>
                  <div className="grid grid-cols-2 gap-3">
                    <label>Total<input inputMode="decimal" value={fields.amount} onChange={(event) => setFields({ ...fields, amount: event.target.value })} placeholder="0.00" /></label>
                    <label>Date<input type="date" value={fields.date} onChange={(event) => setFields({ ...fields, date: event.target.value })} /></label>
                  </div>
                  {!fields.amount && <p className="scan-warning">Total was not found. Enter it here before continuing.</p>}
                  <div className="grid grid-cols-2 gap-3 pt-1">
                    <button onClick={reset} className="preview-secondary">Retake</button>
                    <button onClick={useResult} disabled={!fields.amount} className="preview-primary">Use details</button>
                  </div>
                </div>
              )}

              {status === 'error' && (
                <div className="scan-error">
                  <strong>Scan unsuccessful</strong>
                  <p>{error}</p>
                  <div className="grid grid-cols-2 gap-3">
                    <button onClick={() => cameraInput.current?.click()} className="preview-secondary">Take photo</button>
                    <button onClick={() => galleryInput.current?.click()} className="preview-primary">Upload another</button>
                  </div>
                </div>
              )}
            </section>
          )}
        </div>
      </main>
    </div>
  )
}
