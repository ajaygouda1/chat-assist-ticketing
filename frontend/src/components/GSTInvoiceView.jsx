import React, { useEffect, useState } from 'react';
import { Ticket, Download, CheckCircle2, ArrowRight, Send, RefreshCw, Smartphone } from 'lucide-react';
import { QRCodeSVG } from 'qrcode.react';
import axios from 'axios';
import EventDayPassModal from './tickets/EventDayPassModal';
import TransferTicketModal from './tickets/TransferTicketModal';

export default function GSTInvoiceView({ onNavigateToChat }) {
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedDayPass, setSelectedDayPass] = useState(null);
  const [transferTicketId, setTransferTicketId] = useState(null);

  useEffect(() => {
    fetchUserTickets();
  }, []);

  const fetchUserTickets = async () => {
    try {
      const res = await axios.get('/api/v1/user/tickets');
      setTickets(res.data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleRequestRefund = async (ticketId) => {
    if (!window.confirm("Are you sure you want to request a refund for this ticket?")) return;
    try {
      const res = await axios.post('/api/v1/refunds/request', { ticket_id: ticketId, reason: 'Customer requested refund' });
      alert(`Refund Request Submitted! Eligible Amount: ₹${res.data.eligible_amount}`);
      fetchUserTickets();
    } catch (err) {
      alert(err.response?.data?.detail || 'Refund request failed');
    }
  };

  return (
    <div style={{ padding: '0 24px 40px 24px' }}>
      {selectedDayPass && (
        <EventDayPassModal ticket={selectedDayPass} onClose={() => setSelectedDayPass(null)} />
      )}
      {transferTicketId && (
        <TransferTicketModal ticketId={transferTicketId} onClose={() => { setTransferTicketId(null); fetchUserTickets(); }} />
      )}

      <div style={{ marginBottom: '24px' }}>
        <h2 style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--paper)' }} className="font-display-title">
          My Booked Ticket Pass Vault
        </h2>
        <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
          Your tickets and secure QR passes — View, download GST invoices, transfer passes, or enter Event-Day Mode.
        </p>
      </div>

      {loading ? (
        <div style={{ color: 'var(--text-muted)', padding: '20px' }}>Loading ticket passes...</div>
      ) : tickets.length === 0 ? (
        <div className="glass-panel" style={{ padding: '50px 24px', textAlign: 'center', maxWidth: '520px', margin: '40px auto' }}>
          <Ticket size={52} color="var(--gold)" style={{ margin: '0 auto 16px auto', opacity: 0.8 }} />
          <h3 style={{ fontSize: '1.4rem', color: 'var(--paper)', marginBottom: '8px' }} className="font-display-title">
            No Booked Passes Yet
          </h3>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '20px', lineHeight: '1.5' }}>
            Book your first event pass and access your offline-ready QR gate check-in stub right here.
          </p>
          <button
            onClick={() => {
              if (onNavigateToChat) onNavigateToChat();
            }}
            className="gradient-btn"
            style={{ margin: '0 auto', border: 'none', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '8px' }}
          >
            Find Something Happening This Weekend <ArrowRight size={16} />
          </button>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: '24px' }}>
          {tickets.map(t => (
            <div key={t.id} className="ticket-stub" style={{ padding: '22px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                  <span className="badge badge-grounded">
                    <CheckCircle2 size={12} /> {t.status}
                  </span>
                  <span className="font-mono-data" style={{ fontSize: '0.85rem', color: 'var(--gold)', fontWeight: 700 }}>
                    {t.ticket_number}
                  </span>
                </div>

                <h3 style={{ fontSize: '1.3rem', fontWeight: 800, color: 'var(--paper)', marginBottom: '4px' }} className="font-display-title">
                  {t.event_title}
                </h3>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '16px' }}>
                  {t.location} • {t.date_str}
                </p>

                {/* Real Scannable Vector SVG QR Code */}
                <div style={{ background: '#FFFFFF', padding: '14px', borderRadius: '12px', display: 'flex', flexDirection: 'column', alignItems: 'center', marginBottom: '16px', boxShadow: '0 6px 18px rgba(0,0,0,0.3)' }}>
                  <QRCodeSVG
                    value={t.qr_token || t.ticket_number || String(t.id)}
                    size={150}
                    level="H"
                    includeMargin={true}
                  />
                  <span className="font-mono-data" style={{ fontSize: '0.68rem', color: '#151316', fontWeight: 800, marginTop: '8px', letterSpacing: '0.5px' }}>
                    HMAC SIGNED GATE PASS
                  </span>
                </div>

                {/* Action Buttons for Ticket Management */}
                {t.status === 'CONFIRMED' && (
                  <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
                    <button
                      onClick={() => setSelectedDayPass(t)}
                      style={{ flex: 1, background: 'rgba(34, 197, 94, 0.15)', border: '1px solid #22c55e', color: '#4ade80', padding: '6px 10px', borderRadius: '6px', fontSize: '0.75rem', fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px' }}
                    >
                      <Smartphone size={12} /> Day Pass
                    </button>
                    <button
                      onClick={() => setTransferTicketId(t.id)}
                      style={{ flex: 1, background: 'rgba(99, 102, 241, 0.15)', border: '1px solid #6366f1', color: '#818cf8', padding: '6px 10px', borderRadius: '6px', fontSize: '0.75rem', fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px' }}
                    >
                      <Send size={12} /> Transfer
                    </button>
                    <button
                      onClick={() => handleRequestRefund(t.id)}
                      style={{ flex: 1, background: 'rgba(239, 68, 68, 0.15)', border: '1px solid #ef4444', color: '#f87171', padding: '6px 10px', borderRadius: '6px', fontSize: '0.75rem', fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px' }}
                    >
                      <RefreshCw size={12} /> Refund
                    </button>
                  </div>
                )}
              </div>

              <div className="ticket-seam" />

              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingTop: '4px' }}>
                <div>
                  <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Paid Amount</span>
                  <span className="font-mono-data" style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--gold)' }}>
                    ₹{Number(t.price_paid || 0).toFixed(2)}
                  </span>
                </div>

                <a 
                  href={`/api/v1/invoices/INV-2026-${t.ticket_number.split('-')[1] || '001'}`} 
                  target="_blank" 
                  rel="noreferrer"
                  className="gradient-btn"
                  style={{ padding: '8px 14px', fontSize: '0.8rem', borderRadius: '8px', textDecoration: 'none' }}
                >
                  <Download size={14} /> GST Invoice
                </a>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

