import React, { useState } from 'react';
import { LogIn, UserPlus, ShieldCheck, Lock, Mail, User, Building, AlertCircle } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export default function AuthModal({ isOpen, onClose, initialMode = 'login' }) {
  const [mode, setMode] = useState(initialMode); // 'login', 'register', 'apply-organizer'
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [orgName, setOrgName] = useState('');
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  const { login, register, applyOrganizer, loading, user } = useAuth();

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccessMsg('');

    if (mode === 'login') {
      const res = await login(email, password);
      if (res.success) {
        onClose();
      } else {
        setError(res.message);
      }
    } else if (mode === 'register') {
      if (!name.trim()) {
        setError('Please enter your full name');
        return;
      }
      const res = await register(name, email, password);
      if (res.success) {
        setSuccessMsg('Account created successfully! Logged in as User.');
        setTimeout(() => onClose(), 1000);
      } else {
        setError(res.message);
      }
    } else if (mode === 'apply-organizer') {
      const res = await applyOrganizer(orgName || name || 'Event Management');
      if (res.success) {
        setSuccessMsg('Application APPROVED! You are now an Event Organizer.');
        setTimeout(() => onClose(), 1200);
      } else {
        setError(res.message);
      }
    }
  };

  const handleQuickLogin = (demoEmail, demoPassword) => {
    setEmail(demoEmail);
    setPassword(demoPassword);
    login(demoEmail, demoPassword).then(res => {
      if (res.success) onClose();
      else setError(res.message);
    });
  };

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.75)', backdropFilter: 'blur(8px)', zIndex: 2000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px' }}>
      <div className="glass-panel" style={{ width: '100%', maxWidth: '440px', padding: '32px', border: '1px solid var(--border-glass)' }}>
        
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
          <div>
            <h2 style={{ fontSize: '1.4rem', fontWeight: 800, color: 'white', display: 'flex', alignItems: 'center', gap: '8px' }}>
              {mode === 'login' && <><LogIn color="#60A5FA" size={22} /> Login to ChatAssist</>}
              {mode === 'register' && <><UserPlus color="#34D399" size={22} /> Create Account</>}
              {mode === 'apply-organizer' && <><Building color="#FACC15" size={22} /> Apply as Event Organizer</>}
            </h2>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '4px' }}>
              {mode === 'login' ? 'Enter credentials to access your tickets & organizer tools' :
               mode === 'register' ? 'Sign up for a free account (default role: Customer)' :
               'Upgrade account role to create & manage event listings'}
            </p>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', fontSize: '1.2rem', cursor: 'pointer' }}>✕</button>
        </div>

        {error && (
          <div style={{ background: 'rgba(239, 68, 68, 0.15)', border: '1px solid #F87171', borderRadius: '8px', padding: '10px 14px', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.8rem', color: '#F87171' }}>
            <AlertCircle size={16} flexShrink={0} /> {error}
          </div>
        )}

        {successMsg && (
          <div style={{ background: 'rgba(16, 185, 129, 0.15)', border: '1px solid #34D399', borderRadius: '8px', padding: '10px 14px', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.8rem', color: '#34D399' }}>
            <ShieldCheck size={16} flexShrink={0} /> {successMsg}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          
          {mode === 'register' && (
            <div>
              <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>Full Name</label>
              <div style={{ position: 'relative' }}>
                <User size={18} color="var(--text-muted)" style={{ position: 'absolute', left: '12px', top: '12px' }} />
                <input
                  type="text"
                  placeholder="Ajay Kumar"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  style={{ width: '100%', background: 'rgba(15, 23, 42, 0.7)', border: '1px solid var(--border-glass)', borderRadius: '8px', padding: '10px 12px 10px 40px', color: 'white', fontSize: '0.9rem', outline: 'none' }}
                />
              </div>
            </div>
          )}

          {mode !== 'apply-organizer' && (
            <>
              <div>
                <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>Email Address</label>
                <div style={{ position: 'relative' }}>
                  <Mail size={18} color="var(--text-muted)" style={{ position: 'absolute', left: '12px', top: '12px' }} />
                  <input
                    type="email"
                    placeholder="user@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    style={{ width: '100%', background: 'rgba(15, 23, 42, 0.7)', border: '1px solid var(--border-glass)', borderRadius: '8px', padding: '10px 12px 10px 40px', color: 'white', fontSize: '0.9rem', outline: 'none' }}
                  />
                </div>
              </div>

              <div>
                <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>Password</label>
                <div style={{ position: 'relative' }}>
                  <Lock size={18} color="var(--text-muted)" style={{ position: 'absolute', left: '12px', top: '12px' }} />
                  <input
                    type="password"
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    style={{ width: '100%', background: 'rgba(15, 23, 42, 0.7)', border: '1px solid var(--border-glass)', borderRadius: '8px', padding: '10px 12px 10px 40px', color: 'white', fontSize: '0.9rem', outline: 'none' }}
                  />
                </div>
              </div>
            </>
          )}

          {mode === 'apply-organizer' && (
            <div>
              <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>Organization / Company Name</label>
              <div style={{ position: 'relative' }}>
                <Building size={18} color="var(--text-muted)" style={{ position: 'absolute', left: '12px', top: '12px' }} />
                <input
                  type="text"
                  placeholder="e.g. TechEvents India Studio"
                  value={orgName}
                  onChange={(e) => setOrgName(e.target.value)}
                  style={{ width: '100%', background: 'rgba(15, 23, 42, 0.7)', border: '1px solid var(--border-glass)', borderRadius: '8px', padding: '10px 12px 10px 40px', color: 'white', fontSize: '0.9rem', outline: 'none' }}
                />
              </div>
            </div>
          )}

          <button type="submit" className="gradient-btn" disabled={loading} style={{ padding: '12px', justifyContent: 'center', marginTop: '8px' }}>
            {loading ? 'Processing...' : mode === 'login' ? 'Sign In' : mode === 'register' ? 'Create Account' : 'Submit Application (Instant Approve)'}
          </button>
        </form>

        {/* Mode Switchers */}
        <div style={{ marginTop: '20px', borderTop: '1px solid var(--border-glass)', paddingTop: '16px', textAlign: 'center', fontSize: '0.8rem' }}>
          {mode === 'login' ? (
            <p style={{ color: 'var(--text-muted)' }}>
              Don't have an account?{' '}
              <button onClick={() => { setMode('register'); setError(''); }} style={{ background: 'none', border: 'none', color: '#60A5FA', fontWeight: 600, cursor: 'pointer' }}>
                Create Account
              </button>
            </p>
          ) : (
            <p style={{ color: 'var(--text-muted)' }}>
              Already registered?{' '}
              <button onClick={() => { setMode('login'); setError(''); }} style={{ background: 'none', border: 'none', color: '#60A5FA', fontWeight: 600, cursor: 'pointer' }}>
                Log in
              </button>
            </p>
          )}
        </div>

        {/* Quick Demo Logins (§54b & Demo Accounts) */}
        {mode === 'login' && (
          <div style={{ marginTop: '16px', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-glass)', padding: '12px', borderRadius: '10px' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '8px' }}>Quick Demo Accounts:</span>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <button
                onClick={() => handleQuickLogin('ajaymgouda999@gmail.com', 'superadmin123')}
                style={{ background: 'rgba(59, 130, 246, 0.15)', border: '1px solid #60A5FA', color: '#60A5FA', padding: '6px 10px', borderRadius: '6px', cursor: 'pointer', fontSize: '0.75rem', textAlign: 'left', display: 'flex', justifyContent: 'space-between' }}
              >
                <span>🔑 Super Admin (`ajaymgouda999@gmail.com`)</span>
                <span style={{ fontWeight: 700 }}>super_admin</span>
              </button>
              <button
                onClick={() => handleQuickLogin('organizer@techconf.com', 'password123')}
                style={{ background: 'rgba(16, 185, 129, 0.15)', border: '1px solid #34D399', color: '#34D399', padding: '6px 10px', borderRadius: '6px', cursor: 'pointer', fontSize: '0.75rem', textAlign: 'left', display: 'flex', justifyContent: 'space-between' }}
              >
                <span>🏢 Organizer (`organizer@techconf.com`)</span>
                <span style={{ fontWeight: 700 }}>organizer</span>
              </button>
              <button
                onClick={() => handleQuickLogin('demo@chatassist.com', 'password123')}
                style={{ background: 'rgba(234, 179, 8, 0.15)', border: '1px solid #FACC15', color: '#FACC15', padding: '6px 10px', borderRadius: '6px', cursor: 'pointer', fontSize: '0.75rem', textAlign: 'left', display: 'flex', justifyContent: 'space-between' }}
              >
                <span>👤 Customer (`demo@chatassist.com`)</span>
                <span style={{ fontWeight: 700 }}>customer</span>
              </button>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
