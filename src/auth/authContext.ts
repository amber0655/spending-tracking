import { createContext } from 'react'
import type { User } from 'firebase/auth'
import type {
  sendPasswordReset,
  signInWithEmail,
  signInWithGoogle,
  signOutUser,
  signUpWithEmail,
} from '../services/auth'

export type AuthContextValue = {
  user: User | null
  loading: boolean
  signIn: typeof signInWithEmail
  signUp: typeof signUpWithEmail
  signInWithGoogle: typeof signInWithGoogle
  signOut: typeof signOutUser
  resetPassword: typeof sendPasswordReset
}

export const AuthContext = createContext<AuthContextValue | null>(null)
