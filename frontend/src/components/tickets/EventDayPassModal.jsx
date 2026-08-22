import React from 'react';

export default function EventDayPassModal({ ticket, onClose }) {
  if (!ticket) return null;

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      background: 'rgba(0,0,0,0.85)',
      backdropFilter: 'blur(6px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 9999,
      padding: '16px'
    }}>
      <div style={{
        background: 'linear-gradient(180deg, #0f172a 0%, #1e1b4b 100%)',
        border: '2px solid #6366f1',
        borderRadius: '24px',
        padding: '32px',
        color: '#fff',
        maxWidth: '420px',
        width: '100%',
        textAlign: 'center',
        boxShadow: '0 0 40px rgba(99, 102, 241, 0.4)'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <span style={{ background: '#22c55e', color: '#000', fontSize: '11px', fontWeight: 800, padding: '4px 10px', borderRadius: '12px', textTransform: 'uppercase', letterSpacing: '1px' }}>
            ● EVENT TODAY
          </span>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: '#94a3b8', fontSize: '20px', cursor: 'pointer' }}>✕</button>
        </div>

        <h2 style={{ fontSize: '22px', fontWeight: 700, margin: '0 0 6px', color: '#fff' }}>{ticket.event_title || 'Live Event Pass'}</h2>
        <p style={{ fontSize: '13px', color: '#a5b4fc', margin: '0 0 20px' }}>Gate Entry & High-Contrast QR Code</p>

        {/* Large QR Display */}
        <div style={{
          background: '#fff',
          padding: '20px',
          borderRadius: '16px',
          display: 'inline-block',
          marginBottom: '20px',
          boxShadow: '0 0 20px rgba(255,255,255,0.2)'
        }}>
          {ticket.qr_code_url ? (
            <img src={ticket.qr_code_url} alt="QR Code" style={{ width: '220px', height: '220px', display: 'block' }} />
          ) : (
            <div style={{ width: '220px', height: '220px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#000', fontWeight: 700 }}>
              [ HIGH-BRIGHTNESS QR ]
            </div>
          )}
        </div>

        <div style={{ background: 'rgba(255,255,255,0.05)', borderRadius: '12px', padding: '14px', marginBottom: '20px', textAlign: 'left', fontSize: '13px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
            <span style={{ color: '#94a3b8' }}>Ticket Number:</span>
            <span style={{ fontWeight: 600, color: '#38bdf8' }}>{ticket.ticket_number}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
            <span style={{ color: '#94a3b8' }}>Gate Entrance:</span>
            <span style={{ fontWeight: 600, color: '#22c55e' }}>Gate A — Main Entrance</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: '#94a3b8' }}>Status:</span>
            <span style={{ fontWeight: 600, color: '#22c55e' }}>{ticket.status}</span>
          </div>
        </div>

        <button
          onClick={() => alert('Opening map directions to venue...')}
          style={{
            width: '100%',
            background: 'linear-gradient(90deg, #6366f1, #a855f7)',
            color: '#fff',
            border: 'none',
            padding: '12px',
            borderRadius: '10px',
            fontWeight: 600,
            cursor: 'pointer',
            fontSize: '14px'
          }}
        >
          📍 Get Directions to Venue
        </button>
      </div>
    </div>
  );
}
