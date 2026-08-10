import React, { useState } from 'react';
import { Ticket, Bot, ShieldAlert, Cpu, Sparkles, Search, User, LogIn, LogOut, ShieldCheck, Building } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import AuthModal from './auth/AuthModal';

export default function Navbar({ activeTab, setActiveTab, toggleCopilot, isCopilotOpen, searchQuery, setSearchQuery, onSemanticSearch }) {
  const { user, logout } = useAuth();
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [authModalMode, setAuthModalMode] = useState('login');

  const openAuth = (mode = 'login') => {
    setAuthModalMode(mode);
    setIsAuthModalOpen(true);
  };

  return (
    <>
      <header className="glass-panel" style={{ margin: '16px 24px', padding: '14px 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        {/* Brand */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', cursor: 'pointer' }} onClick={() => setActiveTab('events')}>
          <div style={{ background: 'linear-gradient(135deg, #3B82F6, #8B5CF6)', padding: '10px', borderRadius: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Ticket color="white" size={24} />
          </div>
          <div>
            <h1 style={{ fontSize: '1.25rem', fontWeight: 800 }} className="gradient-text">ChatAssist</h1>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>AI-Powered Ticketing & Support</p>
          </div>
        </div>

        {/* Semantic Search Bar */}
        <form 
          onSubmit={(e) => { e.preventDefault(); onSemanticSearch(searchQuery); }}
          style={{ flex: 1, maxWidth: '360px', display: 'flex', alignItems: 'center', background: 'rgba(255, 255, 255, 0.05)', border: '1px solid var(--border-glass)', borderRadius: '12px', padding: '6px 14px' }}
        >
          <Search size={18} color="var(--text-muted)" style={{ marginRight: '8px' }} />
          <input
            type="text"
            placeholder="Semantic search: 'chill outdoor concert'..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{ background: 'transparent', border: 'none', color: 'white', outline: 'none', width: '100%', fontSize: '0.875rem' }}
          />
          <button type="submit" style={{ background: 'none', border: 'none', color: '#60A5FA', cursor: 'pointer', fontSize: '0.75rem', fontWeight: 600 }}>Vector</button>
        </form>

        {/* Navigation Tabs */}
        <nav style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            onClick={() => setActiveTab('events')}
            style={{ background: activeTab === 'events' ? 'rgba(59, 130, 246, 0.2)' : 'transparent', color: activeTab === 'events' ? '#60A5FA' : 'var(--text-muted)', border: 'none', padding: '8px 14px', borderRadius: '8px', cursor: 'pointer', fontWeight: 600, fontSize: '0.875rem' }}
          >
            Explore Events
          </button>

          <button
            onClick={() => setActiveTab('my-tickets')}
            style={{ background: activeTab === 'my-tickets' ? 'rgba(59, 130, 246, 0.2)' : 'transparent', color: activeTab === 'my-tickets' ? '#60A5FA' : 'var(--text-muted)', border: 'none', padding: '8px 14px', borderRadius: '8px', cursor: 'pointer', fontWeight: 600, fontSize: '0.875rem' }}
          >
            My Tickets & Invoices
          </button>

          <button
            onClick={() => setActiveTab('organizer-studio')}
            style={{ background: activeTab === 'organizer-studio' ? 'rgba(59, 130, 246, 0.2)' : 'transparent', color: activeTab === 'organizer-studio' ? '#60A5FA' : 'var(--text-muted)', border: 'none', padding: '8px 14px', borderRadius: '8px', cursor: 'pointer', fontWeight: 600, fontSize: '0.875rem' }}
          >
            Organizer Studio
          </button>

          <button
            onClick={() => setActiveTab('qr-checkin')}
            style={{ background: activeTab === 'qr-checkin' ? 'rgba(16, 185, 129, 0.2)' : 'transparent', color: activeTab === 'qr-checkin' ? '#34D399' : 'var(--text-muted)', border: 'none', padding: '8px 14px', borderRadius: '8px', cursor: 'pointer', fontWeight: 600, fontSize: '0.875rem', display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            <User flexShrink={0} size={16} /> QR Gate Check-In
          </button>

          <button
            onClick={() => setActiveTab('super-admin')}
            style={{ background: activeTab === 'super-admin' ? 'rgba(59, 130, 246, 0.2)' : 'transparent', color: activeTab === 'super-admin' ? '#60A5FA' : 'var(--text-muted)', border: 'none', padding: '8px 14px', borderRadius: '8px', cursor: 'pointer', fontWeight: 600, fontSize: '0.875rem' }}
          >
            Super Admin
          </button>

          <button
            onClick={() => setActiveTab('concurrency')}
            style={{ background: activeTab === 'concurrency' ? 'rgba(139, 92, 246, 0.2)' : 'transparent', color: activeTab === 'concurrency' ? '#C084FC' : 'var(--text-muted)', border: 'none', padding: '8px 14px', borderRadius: '8px', cursor: 'pointer', fontWeight: 600, fontSize: '0.875rem', display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            <Cpu size={16} /> Load Test
          </button>

          <button
            onClick={() => setActiveTab('fraud')}
            style={{ background: activeTab === 'fraud' ? 'rgba(239, 68, 68, 0.2)' : 'transparent', color: activeTab === 'fraud' ? '#F87171' : 'var(--text-muted)', border: 'none', padding: '8px 14px', borderRadius: '8px', cursor: 'pointer', fontWeight: 600, fontSize: '0.875rem', display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            <ShieldAlert size={16} /> Admin Fraud
          </button>

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

            {/* AI Copilot Drawer Toggle */}
            <button
              onClick={toggleCopilot}
              className="gradient-btn"
              style={{ padding: '8px 14px', fontSize: '0.8rem' }}
            >
              <Bot size={16} /> Copilot
            </button>
          </div>
        </nav>
      </header>

      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
        initialMode={authModalMode}
      />
    </>
  );
}
