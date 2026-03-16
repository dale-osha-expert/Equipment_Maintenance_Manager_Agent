import React from 'react'
import { loginWithGoogle, logout } from '../services/api.js'

const styles = {
  container: { display: 'flex', alignItems: 'center', gap: '10px' },
  email: { fontSize: '14px', color: '#4a5568' },
  btn: {
    padding: '8px 16px',
    borderRadius: '8px',
    border: 'none',
    cursor: 'pointer',
    fontFamily: 'Inter, sans-serif',
    fontSize: '14px',
    fontWeight: 600,
    transition: 'opacity 0.2s',
  },
  loginBtn: { background: '#4285F4', color: '#fff' },
  logoutBtn: { background: '#e53e3e', color: '#fff' },
  dot: { width: 8, height: 8, borderRadius: '50%', background: '#38a169', display: 'inline-block' },
}

export default function AuthButton({ authStatus, onAuthChange }) {
  const handleLogout = async () => {
    await logout()
    onAuthChange()
  }

  if (authStatus?.authenticated) {
    return (
      <div style={styles.container}>
        <span style={styles.dot} />
        <span style={styles.email}>{authStatus.email || 'Connected'}</span>
        <button style={{ ...styles.btn, ...styles.logoutBtn }} onClick={handleLogout}>
          Disconnect Google
        </button>
      </div>
    )
  }

  return (
    <button style={{ ...styles.btn, ...styles.loginBtn }} onClick={loginWithGoogle}>
      Connect Google Account
    </button>
  )
}
