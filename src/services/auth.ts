import {
  GoogleAuthProvider,
  createUserWithEmailAndPassword,
  getRedirectResult,
  onAuthStateChanged,
  sendPasswordResetEmail,
  signInWithEmailAndPassword,
  signInWithPopup,
  signInWithRedirect,
  signOut,
  type NextOrObserver,
  type User,
} from 'firebase/auth'
import { auth } from '../lib/firebase'

const googleProvider = new GoogleAuthProvider()
googleProvider.setCustomParameters({ prompt: 'select_account' })

export function signInWithEmail(email: string, password: string) {
  return signInWithEmailAndPassword(auth, email, password)
}

export function signUpWithEmail(email: string, password: string) {
  return createUserWithEmailAndPassword(auth, email, password)
}

export function signInWithGoogle() {
  const isMobile = /Android|iPhone|iPad|iPod|Mobile/i.test(navigator.userAgent)
  return isMobile
    ? signInWithRedirect(auth, googleProvider)
    : signInWithPopup(auth, googleProvider)
}

let redirectResultPromise: ReturnType<typeof getRedirectResult> | null = null

export function completeGoogleRedirectSignIn() {
  redirectResultPromise ??= getRedirectResult(auth)
  return redirectResultPromise
}

export function signOutUser() {
  return signOut(auth)
}

export function sendPasswordReset(email: string) {
  return sendPasswordResetEmail(auth, email)
}

export function subscribeToAuthState(observer: NextOrObserver<User>) {
  return onAuthStateChanged(auth, observer)
}
