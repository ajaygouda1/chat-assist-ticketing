import React, { useState } from 'react';
import { Ticket, Sparkles, Menu, Compass, MessageSquare, LogIn, LogOut, User, PlusCircle, QrCode } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import AuthModal from './auth/AuthModal';

export default function Navbar({ 
  activeTab, 
  setActiveTab, 
  onToggleSidebar,
  isSidebarOpen 
}) {
  const { user, logout } = useAuth();
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [authModalMode, setAuthModalMode] = useState('login');

  const openAuth = (mode = 'login') => {
    setAuthModalMode(mode);
    setIsAuthModalOpen(true);
  };

  const getInitials = (name) => {
    if (!name) return 'U';
    const parts = name.split(' ');
    return parts.length > 1 ? (parts[0][0] + parts[1][0]).toUpperCase() : parts[0].slice(0, 2).toUpperCase();
  };

  return (
    <>
      <header
        style={{
          height: '60px',
          background: 'var(--bg-primary)',
          borderBottom: '1px solid var(--border)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 20px',
          position: 'sticky',
          top: 0,
          zIndex: 40,
        }}
      >
        {/* Left: Mobile Toggle & Brand */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          {onToggleSidebar && (
            <button
              onClick={onToggleSidebar}
              style={{
                background: 'transparent',
                border: 'none',
                color: 'var(--text-secondary)',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                padding: '6px',
                borderRadius: '6px',
              }}
              aria-label="Toggle chat history"
            >
              <Menu size={20} />
            </button>
          )}

          <div
            onClick={() => setActiveTab('chat')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              cursor: 'pointer',
              userSelect: 'none',
            }}
          >
            <span style={{ color: 'var(--accent)', fontSize: '1.25rem', fontWeight: 700 }}>✦</span>
            <span style={{ color: 'var(--text-primary)', fontSize: '1.05rem', fontWeight: 700, letterSpacing: '-0.02em' }}>
              ChatAssist
            </span>
          </div>
        </div>

        {/* Center / Right: Minimal Navigation */}
        <nav style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <button
            onClick={() => setActiveTab('chat')}
            style={{
              background: activeTab === 'chat' ? 'rgba(255, 255, 255, 0.08)' : 'transparent',
              color: activeTab === 'chat' ? 'var(--text-primary)' : 'var(--text-secondary)',
              border: 'none',
              padding: '7px 13px',
              borderRadius: 'var(--radius-btn)',
              cursor: 'pointer',
              fontWeight: 500,
              fontSize: '0.875rem',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <MessageSquare size={16} />
            <span className="nav-label">Chat</span>
          </button>

          <button
            onClick={() => setActiveTab('events')}
            style={{
              background: activeTab === 'events' ? 'rgba(255, 255, 255, 0.08)' : 'transparent',
              color: activeTab === 'events' ? 'var(--text-primary)' : 'var(--text-secondary)',
              border: 'none',
              padding: '7px 13px',
              borderRadius: 'var(--radius-btn)',
              cursor: 'pointer',
              fontWeight: 500,
              fontSize: '0.875rem',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <Compass size={16} />
            <span className="nav-label">Explore</span>
          </button>

          <button
            onClick={() => setActiveTab('my-tickets')}
            style={{
              background: activeTab === 'my-tickets' ? 'rgba(255, 255, 255, 0.08)' : 'transparent',
              color: activeTab === 'my-tickets' ? 'var(--text-primary)' : 'var(--text-secondary)',
              border: 'none',
              padding: '7px 13px',
              borderRadius: 'var(--radius-btn)',
              cursor: 'pointer',
              fontWeight: 500,
              fontSize: '0.875rem',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <Ticket size={16} />
            <span className="nav-label">My Tickets</span>
          </button>

          {/* Gate Check-In (Organizer) */}
          <button
            onClick={() => setActiveTab('qr-checkin')}
            style={{
              background: activeTab === 'qr-checkin' ? 'rgba(52, 211, 153, 0.15)' : 'transparent',
              color: activeTab === 'qr-checkin' ? '#34D399' : 'var(--text-secondary)',
              border: activeTab === 'qr-checkin' ? '1px solid rgba(52, 211, 153, 0.3)' : 'none',
              padding: '7px 13px',
              borderRadius: 'var(--radius-btn)',
              cursor: 'pointer',
              fontWeight: 500,
              fontSize: '0.875rem',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
            title="Scan ticket QR codes at gate entrance"
          >
            <QrCode size={16} />
            <span className="nav-label">Gate Check-In</span>
          </button>

          {/* Create Event (Organizer) */}
          <button
            onClick={() => setActiveTab('create-event')}
            style={{
              background: activeTab === 'create-event' ? 'rgba(108, 92, 231, 0.2)' : 'transparent',
              color: activeTab === 'create-event' ? 'var(--accent)' : 'var(--text-secondary)',
              border: 'none',
              padding: '7px 13px',
              borderRadius: 'var(--radius-btn)',
              cursor: 'pointer',
              fontWeight: 500,
              fontSize: '0.875rem',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
            title="Create and publish events"
          >
            <PlusCircle size={16} />
            <span className="nav-label">Create</span>
          </button>

          {/* Divider */}
          <div style={{ width: '1px', height: '20px', background: 'var(--border)', margin: '0 6px' }} />

          {/* User Profile / Auth */}
          {user ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div
                title={user.name || user.email}
                style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '50%',
                  background: 'var(--accent)',
                  color: 'white',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '0.8rem',
                  fontWeight: 600,
                }}
              >
                {getInitials(user.name || user.email)}
              </div>
              <button
                onClick={logout}
                title="Logout"
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: 'var(--text-muted)',
                  cursor: 'pointer',
                  padding: '6px',
                  borderRadius: '6px',
                  display: 'flex',
                  alignItems: 'center',
                }}
              >
                <LogOut size={16} />
              </button>
            </div>
          ) : (
            <button
              onClick={() => openAuth('login')}
              style={{
                background: 'transparent',
                border: '1px solid var(--border)',
                color: 'var(--text-primary)',
                padding: '6px 14px',
                borderRadius: 'var(--radius-btn)',
                cursor: 'pointer',
                fontWeight: 500,
                fontSize: '0.825rem',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
              }}
            >
              <LogIn size={14} /> Log in
            </button>
          )}
        </nav>
      </header>

      {/* Auth Modal */}
      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
        initialMode={authModalMode}
      />
    </>
  );
}
