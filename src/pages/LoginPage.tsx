import { type FormEvent, useEffect, useState } from 'react'
import { FirebaseError } from 'firebase/app'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { Icon } from '../components/Icon'
import { useAuth } from '../auth/useAuth'
import { completeGoogleRedirectSignIn } from '../services/auth'

function GoogleMark() {
  return (
    <svg aria-hidden="true" className="size-5" viewBox="0 0 24 24">
      <path fill="#4285F4" d="M21.6 12.2c0-.7-.1-1.5-.2-2.2H12v4.3h5.4a4.6 4.6 0 0 1-2 3v2.8h3.5c2-1.9 3.2-4.6 3.2-7.9Z" />
      <path fill="#34A853" d="M12 22c2.9 0 5.3-1 7-2.6l-3.5-2.8a6.3 6.3 0 0 1-9.4-3.3H2.5v2.8A10 10 0 0 0 12 22Z" />
      <path fill="#FBBC05" d="M6.1 13.3a6 6 0 0 1 0-3.8V6.7H2.5a10 10 0 0 0 0 9.4l3.6-2.8Z" />
      <path fill="#EA4335" d="M12 5.4c1.6 0 3.1.6 4.3 1.7L19.4 4A10.4 10.4 0 0 0 2.5 6.7l3.6 2.8A6 6 0 0 1 12 5.4Z" />
    </svg>
  )
}

function authErrorMessage(error: unknown) {
  if (!(error instanceof FirebaseError)) return 'Something went wrong. Please try again.'

  const messages: Record<string, string> = {
    'auth/email-already-in-use': 'An account already exists for this email.',
    'auth/invalid-credential': 'The email or password is incorrect.',
    'auth/invalid-email': 'Enter a valid email address.',
    'auth/operation-not-allowed': 'Google sign-in is not enabled in Firebase Console.',
    'auth/popup-blocked': 'Allow popups to continue with Google.',
    'auth/popup-closed-by-user': 'Google sign-in was cancelled.',
    'auth/unauthorized-domain': 'This domain is not authorized in Firebase. Use localhost or add this domain in Firebase Console.',
    'auth/too-many-requests': 'Too many attempts. Please try again later.',
    'auth/weak-password': 'Use a password with at least 6 characters.',
  }

  return messages[error.code] ?? `Authentication failed (${error.code}).`
}

export function LoginPage() {
  const [showPassword, setShowPassword] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isSignUp, setIsSignUp] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const { user, loading, signIn, signUp, signInWithGoogle, resetPassword } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const destination = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname ?? '/dashboard'

  useEffect(() => {
    void completeGoogleRedirectSignIn().catch((authError) => {
      setError(authErrorMessage(authError))
      setIsSubmitting(false)
    })
  }, [])

  if (!loading && user) return <Navigate to={destination} replace />

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setNotice('')
    setIsSubmitting(true)
    const form = new FormData(event.currentTarget)
    const email = String(form.get('email') ?? '')
    const password = String(form.get('password') ?? '')

    try {
      if (isSignUp) await signUp(email, password)
      else await signIn(email, password)
      navigate(destination, { replace: true })
    } catch (authError) {
      setError(authErrorMessage(authError))
    } finally {
      setIsSubmitting(false)
    }
  }

  async function handleGoogleSignIn() {
    setError('')
    setNotice('')
    setIsSubmitting(true)
    try {
      await signInWithGoogle()
      navigate(destination, { replace: true })
    } catch (authError) {
      setError(authErrorMessage(authError))
    } finally {
      setIsSubmitting(false)
    }
  }

  async function handlePasswordReset() {
    const emailInput = document.querySelector<HTMLInputElement>('#email')
    const email = emailInput?.value.trim() ?? ''
    if (!email) {
      setError('Enter your email address before requesting a reset link.')
      return
    }
    setError('')
    try {
      await resetPassword(email)
      setNotice('Password reset email sent. Check your inbox.')
    } catch (authError) {
      setError(authErrorMessage(authError))
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-glow auth-glow--mint" />
      <div className="auth-glow auth-glow--blue" />
      <main className="relative z-10 w-full max-w-[440px] animate-enter">
        <header className="mb-10 text-center">
          <div className="mx-auto mb-6 grid size-16 place-items-center rounded-2xl bg-black text-white shadow-xl">
            <Icon name="sparkles" className="size-8 fill-current" />
          </div>
          <h1 className="text-[32px] font-semibold tracking-tight sm:text-[36px]">Aura Finance</h1>
          <p className="mt-2 text-[#45464d]">Step into financial serenity</p>
        </header>

        <section className="rounded-3xl border border-[#c6c6cd]/50 bg-white p-6 shadow-lg sm:p-8">
          <form className="space-y-6" onSubmit={handleSubmit}>
            <div className="space-y-2">
              <label className="field-label" htmlFor="email">Email address</label>
              <div className="field-shell">
                <Icon name="mail" className="field-icon" />
                <input id="email" name="email" type="email" autoComplete="email" placeholder="name@company.com" required className="field-input" />
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between">
                <label className="field-label" htmlFor="password">Password</label>
                {!isSignUp && <button type="button" onClick={handlePasswordReset} className="text-xs font-semibold">Forgot?</button>}
              </div>
              <div className="field-shell">
                <Icon name="lock" className="field-icon" />
                <input id="password" name="password" type={showPassword ? 'text' : 'password'} minLength={6} autoComplete={isSignUp ? 'new-password' : 'current-password'} placeholder="••••••••" required className="field-input pr-12" />
                <button type="button" onClick={() => setShowPassword((visible) => !visible)} aria-label={showPassword ? 'Hide password' : 'Show password'} className="absolute inset-y-0 right-0 grid w-12 place-items-center text-[#76777d]">
                  <Icon name={showPassword ? 'eyeOff' : 'eye'} className="size-5" />
                </button>
              </div>
            </div>

            {error && <p role="alert" className="rounded-xl bg-[#ffdad6] px-4 py-3 text-sm text-[#93000a]">{error}</p>}
            {notice && <p role="status" className="rounded-xl bg-[#6cf8bb]/25 px-4 py-3 text-sm text-[#005236]">{notice}</p>}

            <div className="space-y-4 pt-2">
              <button type="submit" disabled={isSubmitting} className="primary-button">
                {isSubmitting ? <><span className="spinner" /> Please wait…</> : isSignUp ? 'Create account' : 'Sign in with email'}
              </button>
              <div className="flex items-center gap-4 text-xs uppercase text-[#76777d]"><span className="h-px flex-1 bg-[#c6c6cd]" />or<span className="h-px flex-1 bg-[#c6c6cd]" /></div>
              <button type="button" disabled={isSubmitting} onClick={handleGoogleSignIn} className="secondary-button"><GoogleMark />Continue with Google</button>
            </div>
          </form>
        </section>

        <footer className="mt-8 text-center text-sm text-[#45464d]">
          {isSignUp ? 'Already have an account?' : 'New to Aura?'}
          <button type="button" onClick={() => { setIsSignUp((value) => !value); setError(''); setNotice('') }} className="ml-2 font-bold text-black">
            {isSignUp ? 'Sign In' : 'Create Account'}
          </button>
        </footer>
      </main>
    </div>
  )
}
