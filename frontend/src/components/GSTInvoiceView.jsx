import React, { useEffect, useState } from 'react';
import { Ticket, Download, CheckCircle2, ArrowRight } from 'lucide-react';
import axios from 'axios';

export default function GSTInvoiceView() {
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);

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

  return (
    <div style={{ padding: '0 24px 40px 24px' }}>
      <div style={{ marginBottom: '24px' }}>
        <h2 style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--paper)' }} className="font-display-title">
          My Booked Ticket Pass Vault
        </h2>
        <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
          Cryptographic HMAC-SHA256 signed entry passes & downloadable tax invoices (§55b & §56b)
        </p>
      </div>

      {loading ? (
        <div style={{ color: 'var(--text-muted)', padding: '20px' }}>Loading ticket passes...</div>
      ) : tickets.length === 0 ? (
        /* First-run empty state invite (§55c & §56c) */
        <div className="glass-panel" style={{ padding: '50px 24px', textAlign: 'center', maxWidth: '520px', margin: '40px auto' }}>
          <Ticket size={52} color="var(--gold)" style={{ margin: '0 auto 16px auto', opacity: 0.8 }} />
          <h3 style={{ fontSize: '1.4rem', color: 'var(--paper)', marginBottom: '8px' }} className="font-display-title">
            No Booked Passes Yet
          </h3>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '20px', lineHeight: '1.5' }}>
            Book your first event pass and access your offline-ready QR gate check-in stub right here.
          </p>
          <a
            href="#events"
            onClick={(e) => {
              e.preventDefault();
              window.location.hash = '#events';
              window.dispatchEvent(new HashChangeEvent('hashchange'));
            }}
            className="gradient-btn"
            style={{ margin: '0 auto', textDecoration: 'none' }}
          >
            Find Something Happening This Weekend <ArrowRight size={16} />
          </a>
        </div>
      ) : (
        /* Ticket Stubs Grid (§55b) */
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

                {/* QR Code Pass Display */}
                {t.qr_data_url && (
                  <div style={{ background: '#FFFFFF', padding: '14px', borderRadius: '12px', display: 'flex', flexDirection: 'column', alignItems: 'center', marginBottom: '16px', boxShadow: '0 6px 18px rgba(0,0,0,0.3)' }}>
                    <img src={t.qr_data_url} alt={`QR Pass for ${t.ticket_number}`} style={{ width: '150px', height: '150px' }} />
                    <span className="font-mono-data" style={{ fontSize: '0.65rem', color: '#151316', fontWeight: 800, marginTop: '8px', letterSpacing: '0.5px' }}>
                      HMAC SIGNED GATE PASS
                    </span>
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
                  <Download size={14} /> GST Invoice (PDF)
                </a>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
