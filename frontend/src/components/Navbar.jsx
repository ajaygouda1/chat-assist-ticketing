import React, { useState } from 'react';
import { Ticket, Bot, ShieldAlert, Cpu, Sparkles, Search, User, LogIn, LogOut, ShieldCheck, Building } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import AuthModal from './auth/AuthModal';
import NotificationCenter from './notifications/NotificationCenter';

export default function Navbar({ activeTab, setActiveTab, toggleCopilot, isCopilotOpen, searchQuery, setSearchQuery, onSemanticSearch, onOpenCreateWizard }) {
  const { user, logout } = useAuth();
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [authModalMode, setAuthModalMode] = useState('login');
  const [isNotifCenterOpen, setIsNotifCenterOpen] = useState(false);

  const openAuth = (mode = 'login') => {
    setAuthModalMode(mode);
    setIsAuthModalOpen(true);
  };

  return (
    <>
      <header className="glass-panel" style={{ margin: '16px 24px', padding: '14px 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        {/* Brand */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', cursor: 'pointer' }} onClick={() => setActiveTab('chat')}>
          <div style={{ background: 'linear-gradient(135deg, #8B5CF6, #EC4899)', padding: '10px', borderRadius: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Bot color="white" size={24} />
          </div>
          <div>
            <h1 style={{ fontSize: '1.25rem', fontWeight: 800 }} className="gradient-text">ChatAssist</h1>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Conversational AI Ticketing Engine</p>
          </div>
        </div>

        {/* Semantic Search Bar */}
        <form 
          onSubmit={(e) => { e.preventDefault(); onSemanticSearch(searchQuery); setActiveTab('chat'); }}
          style={{ flex: 1, maxWidth: '360px', display: 'flex', alignItems: 'center', background: 'rgba(255, 255, 255, 0.05)', border: '1px solid var(--border-glass)', borderRadius: '12px', padding: '6px 14px' }}
        >
          <Search size={18} color="var(--text-muted)" style={{ marginRight: '8px' }} />
          <input
            type="text"
            placeholder="Ask AI or search: 'chill outdoor concert'..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{ background: 'transparent', border: 'none', color: 'white', outline: 'none', width: '100%', fontSize: '0.875rem' }}
          />
          <button type="submit" style={{ background: 'none', border: 'none', color: '#A78BFA', cursor: 'pointer', fontSize: '0.75rem', fontWeight: 600 }}>Vector</button>
        </form>

        {/* Navigation Tabs */}
        <nav style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
          {/* Top-Level Create Event Button */}
          <button
            onClick={() => setActiveTab('create-event')}

            style={{
              background: 'linear-gradient(135deg, #10B981, #059669)',
              color: 'white',
              border: 'none',
              padding: '8px 16px',
              borderRadius: '10px',
              cursor: 'pointer',
              fontWeight: 700,
              fontSize: '0.875rem',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              boxShadow: '0 4px 12px rgba(16, 185, 129, 0.3)'
            }}
          >
            <Sparkles size={16} /> + Create Event
          </button>

          <button
            onClick={() => setActiveTab('chat')}
            style={{
              background: activeTab === 'chat' ? 'linear-gradient(135deg, #8B5CF6, #6366F1)' : 'rgba(139, 92, 246, 0.15)',
              color: activeTab === 'chat' ? 'white' : '#C4B5FD',
              border: '1px solid rgba(139, 92, 246, 0.4)',
              padding: '8px 16px',
              borderRadius: '10px',
              cursor: 'pointer',
              fontWeight: 700,
              fontSize: '0.875rem',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            <Bot size={16} /> Chat
          </button>

          <button
            onClick={() => setActiveTab('my-tickets')}
            style={{
              background: activeTab === 'my-tickets' ? 'rgba(59, 130, 246, 0.2)' : 'transparent',
              color: activeTab === 'my-tickets' ? '#60A5FA' : 'var(--text-muted)',
              border: activeTab === 'my-tickets' ? '1px solid rgba(59, 130, 246, 0.4)' : '1px solid transparent',
              padding: '8px 14px',
              borderRadius: '10px',
              cursor: 'pointer',
              fontWeight: 600,
              fontSize: '0.825rem',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            <Ticket size={16} /> My Tickets
          </button>

          <button
            onClick={() => setActiveTab('events')}
            style={{
              background: activeTab === 'events' ? 'rgba(59, 130, 246, 0.2)' : 'transparent',
              color: activeTab === 'events' ? '#60A5FA' : 'var(--text-muted)',
              border: activeTab === 'events' ? '1px solid rgba(59, 130, 246, 0.4)' : '1px solid transparent',
              padding: '8px 14px',
              borderRadius: '10px',
              cursor: 'pointer',
              fontWeight: 600,
              fontSize: '0.825rem'
            }}
          >
            Explore
          </button>


          {/* Notification Bell */}
          <button
            onClick={() => setIsNotifCenterOpen(!isNotifCenterOpen)}
            title="Notifications"
            style={{
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid var(--border-glass)',
              color: '#F1F5F9',
              padding: '8px',
              borderRadius: '10px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              position: 'relative'
            }}
          >
            🔔
          </button>

          {/* Tools Menu (Organizers & Admins) */}
          <div style={{ position: 'relative', display: 'inline-block' }}>
            <select
              value={['organizer-studio', 'qr-checkin', 'super-admin', 'concurrency', 'fraud'].includes(activeTab) ? activeTab : ''}
              onChange={(e) => {
                if (e.target.value) setActiveTab(e.target.value);
              }}
              style={{
                background: ['organizer-studio', 'qr-checkin', 'super-admin', 'concurrency', 'fraud'].includes(activeTab) ? 'rgba(16, 185, 129, 0.2)' : 'rgba(255,255,255,0.05)',
                color: ['organizer-studio', 'qr-checkin', 'super-admin', 'concurrency', 'fraud'].includes(activeTab) ? '#34D399' : 'var(--text-muted)',
                border: '1px solid var(--border-glass)',
                padding: '8px 12px',
                borderRadius: '10px',
                cursor: 'pointer',
                fontWeight: 600,
                fontSize: '0.8rem',
                outline: 'none'
              }}
            >
              <option value="" disabled style={{ background: '#0F172A', color: '#94A3B8' }}>🛠️ Platform Tools</option>
              <option value="organizer-studio" style={{ background: '#0F172A', color: 'white' }}>Organizer Studio</option>
              <option value="qr-checkin" style={{ background: '#0F172A', color: 'white' }}>QR Gate Check-In</option>
              <option value="super-admin" style={{ background: '#0F172A', color: 'white' }}>Super Admin</option>
              <option value="fraud" style={{ background: '#0F172A', color: 'white' }}>Fraud Shield</option>
              <option value="concurrency" style={{ background: '#0F172A', color: 'white' }}>Concurrency Engine</option>
            </select>
          </div>

          {/* User Account / Auth Section */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', borderLeft: '1px solid var(--border-glass)', paddingLeft: '12px', marginLeft: '4px' }}>
            {user ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{ textAlign: 'right' }}>
                  <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'white', display: 'block' }}>{user.name}</span>
                  <span style={{
                    fontSize: '0.65rem',
                    fontWeight: 800,
                    padding: '1px 6px',
                    borderRadius: '4px',
                    textTransform: 'uppercase',
                    background: user.role === 'super_admin' ? 'rgba(239, 68, 68, 0.2)' : user.role === 'organizer' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(59, 130, 246, 0.2)',
                    color: user.role === 'super_admin' ? '#F87171' : user.role === 'organizer' ? '#34D399' : '#60A5FA',
                    border: user.role === 'super_admin' ? '1px solid #F87171' : user.role === 'organizer' ? '1px solid #34D399' : '1px solid #60A5FA'
                  }}>
                    {user.role}
                  </span>
                </div>

                {user.role === 'customer' && (
                  <button
                    onClick={() => openAuth('apply-organizer')}
                    title="Apply to become an Event Organizer"
                    style={{ background: 'rgba(234, 179, 8, 0.15)', border: '1px solid #FACC15', color: '#FACC15', padding: '6px 10px', borderRadius: '8px', cursor: 'pointer', fontSize: '0.75rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '4px' }}
                  >
                    <Building size={14} /> Become Organizer
                  </button>
                )}

                <button
                  onClick={logout}
                  title="Sign Out"
                  style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border-glass)', color: 'var(--text-muted)', padding: '6px 10px', borderRadius: '8px', cursor: 'pointer', fontSize: '0.75rem' }}
                >
                  <LogOut size={14} />
                </button>
              </div>
            ) : (
              <div style={{ display: 'flex', gap: '6px' }}>
                <button
                  onClick={() => openAuth('login')}
                  style={{ background: 'rgba(59, 130, 246, 0.15)', border: '1px solid #60A5FA', color: '#60A5FA', padding: '6px 12px', borderRadius: '8px', cursor: 'pointer', fontSize: '0.8rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '4px' }}
                >
                  <LogIn size={14} /> Login
                </button>
                <button
                  onClick={() => openAuth('register')}
                  style={{ background: 'rgba(255, 255, 255, 0.08)', border: '1px solid var(--border-glass)', color: 'white', padding: '6px 12px', borderRadius: '8px', cursor: 'pointer', fontSize: '0.8rem', fontWeight: 600 }}
                >
                  Sign Up
                </button>
              </div>
            )}
          </div>
        </nav>
      </header>

      {isNotifCenterOpen && (
        <div style={{ position: 'fixed', top: '80px', right: '30px', zIndex: 9999 }}>
          <NotificationCenter onClose={() => setIsNotifCenterOpen(false)} />
        </div>
      )}

      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
        initialMode={authModalMode}
      />
    </>
  );
}
