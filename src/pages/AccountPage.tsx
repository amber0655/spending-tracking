import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { FirebaseError } from 'firebase/app'
import { useAuth } from '../auth/useAuth'
import { AppHeader, BottomNav } from '../components/AppShell'
import { Icon } from '../components/Icon'

export function AccountPage() {
  const { user, signOut } = useAuth()
  const navigate = useNavigate()
  const [isSigningOut, setIsSigningOut] = useState(false)
  const [error, setError] = useState('')
  const provider = user?.providerData[0]?.providerId === 'google.com' ? 'Google' : 'Email and password'

  async function handleSignOut() {
    setError('')
    setIsSigningOut(true)
    try {
      await signOut()
      navigate('/login', { replace: true })
    } catch (signOutError) {
      setError(signOutError instanceof FirebaseError ? 'Unable to sign out. Please try again.' : 'Something went wrong.')
      setIsSigningOut(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#f7f9fb] text-[#191c1e]">
      <AppHeader />
      <main className="mx-auto max-w-2xl px-5 pb-32 pt-24 sm:px-8">
        <p className="eyebrow text-[#71809a]">Profile and security</p>
        <h2 className="mt-2 text-3xl font-semibold tracking-[-0.02em]">My Account</h2>

        <section className="account-card mt-7">
          <div className="account-avatar">
            {user?.photoURL ? <img src={user.photoURL} alt="" referrerPolicy="no-referrer" /> : <Icon name="user" className="size-8" />}
          </div>
          <div className="min-w-0">
            <h3 className="truncate text-xl font-semibold">{user?.displayName || 'Aura Member'}</h3>
            <p className="mt-1 truncate text-sm text-[#5c5d64]">{user?.email}</p>
          </div>
        </section>

        <section className="account-details mt-5">
          <div><span>Email</span><strong>{user?.email || 'Not available'}</strong></div>
          <div><span>Sign-in method</span><strong>{provider}</strong></div>
          <div><span>Email verified</span><strong>{user?.emailVerified ? 'Verified' : 'Not verified'}</strong></div>
        </section>

        {error && <p role="alert" className="mt-5 rounded-xl bg-[#ffdad6] px-4 py-3 text-sm text-[#93000a]">{error}</p>}

        <button type="button" onClick={handleSignOut} disabled={isSigningOut} className="sign-out-button">
          {isSigningOut ? <span className="spinner" /> : <Icon name="logout" className="size-5" />}
          {isSigningOut ? 'Signing out…' : 'Sign out'}
        </button>
      </main>
      <BottomNav active="account" />
    </div>
  )
}
