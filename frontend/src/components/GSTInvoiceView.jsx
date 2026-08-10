import React, { useEffect, useState } from 'react';
import { Ticket, Download, Calendar, MapPin, FileText, CheckCircle2, QrCode } from 'lucide-react';
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
      setTickets(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '0 24px 40px 24px' }}>
      <div style={{ marginBottom: '24px' }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'white' }}>My Booked Tickets & Entry Passes</h2>
        <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>View confirmed ticket passes, show phone QR entry passes at gate check-in, and download tax invoices</p>
      </div>

      {loading ? (
        <div style={{ color: 'var(--text-muted)', padding: '20px' }}>Loading ticket passes...</div>
      ) : tickets.length === 0 ? (
        <div className="glass-panel" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
          <Ticket size={48} style={{ margin: '0 auto 16px auto', opacity: 0.5 }} />
          <h3>No Booked Tickets Yet</h3>
          <p style={{ fontSize: '0.875rem', marginTop: '8px' }}>Explore upcoming events on the homepage and secure your pass.</p>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: '20px' }}>
          {tickets.map(t => (
            <div key={t.id} className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                  <span className="badge badge-grounded">
                    <CheckCircle2 size={12} /> {t.status}
                  </span>
                  <span style={{ fontSize: '0.75rem', color: '#60A5FA', fontWeight: 700 }}>{t.ticket_number}</span>
                </div>

                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'white', marginBottom: '6px' }}>{t.event_title}</h3>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '16px' }}>{t.location} • {t.date_str}</p>

                {/* QR Code Pass Display */}
                {t.qr_data_url && (
                  <div style={{ background: '#FFFFFF', padding: '12px', borderRadius: '12px', display: 'flex', flexDirection: 'column', alignItems: 'center', marginBottom: '16px', boxShadow: '0 4px 12px rgba(0,0,0,0.2)' }}>
                    <img src={t.qr_data_url} alt="Gate Check-In QR Pass" style={{ width: '140px', height: '140px' }} />
                    <span style={{ fontSize: '0.65rem', color: '#334155', fontWeight: 700, marginTop: '6px', letterSpacing: '0.5px' }}>HMAC SIGNED GATE PASS</span>
                  </div>
                )}
              </div>

              <div style={{ borderTop: '1px solid var(--border-glass)', paddingTop: '16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div>
                  <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block' }}>Paid Amount</span>
                  <span style={{ fontSize: '1.1rem', fontWeight: 700, color: '#34D399' }}>₹{Number(t.price_paid || 0).toFixed(2)}</span>
                </div>

                <a 
                  href={`/api/v1/invoices/INV-2026-${t.ticket_number.split('-')[1]}`} 
                  target="_blank" 
                  rel="noreferrer"
                  className="gradient-btn"
                  style={{ padding: '8px 12px', fontSize: '0.75rem', borderRadius: '8px', textDecoration: 'none' }}
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

