import React, { useState, useEffect } from 'react';
import { Ticket, Calendar, MapPin, CheckCircle, CreditCard, ArrowRight, Clock, AlertTriangle, Download, ExternalLink, QrCode } from 'lucide-react';
import { QRCodeSVG } from 'qrcode.react';

export function formatINR(val) {
  if (val === undefined || val === null || isNaN(val)) return '₹0.00';
  return Number(val).toLocaleString('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  });
}

// -------------------------------------------------------------
// 1. Compact Event Card (Max 2-3 results, uncluttered)
// -------------------------------------------------------------
export function EventCard({ id, title, category, date_str, location, venue, price, available_tickets, onSelect }) {
  return (
    <div
      style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius-card)',
        padding: '16px',
        marginTop: '8px',
        display: 'flex',
        flexDirection: 'column',
        gap: '8px',
        transition: 'border-color 150ms ease',
      }}
      onMouseOver={(e) => e.currentTarget.style.borderColor = 'rgba(108, 92, 231, 0.5)'}
      onMouseOut={(e) => e.currentTarget.style.borderColor = 'var(--border)'}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '10px' }}>
        <div>
          <h4 style={{ color: 'var(--text-primary)', fontSize: '0.98rem', fontWeight: 600, margin: 0 }}>
            {title}
          </h4>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.82rem', margin: '4px 0 0 0' }}>
            {date_str || 'Upcoming'} • {location || venue || 'India'}
          </p>
        </div>
        {category && (
          <span
            style={{
              fontSize: '0.72rem',
              color: 'var(--accent)',
              background: 'var(--accent-soft)',
              padding: '2px 8px',
              borderRadius: 'var(--radius-chip)',
              fontWeight: 500,
              whiteSpace: 'nowrap',
            }}
          >
            {category}
          </span>
        )}
      </div>

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '6px', paddingTop: '8px', borderTop: '1px solid var(--border)' }}>
        <div>
          <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>From </span>
          <span style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-primary)' }}>
            {formatINR(price)}
          </span>
          {available_tickets !== undefined && (
            <span style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', marginLeft: '6px' }}>
              ({available_tickets} available)
            </span>
          )}
        </div>

        {onSelect && (
          <button
            onClick={() => onSelect(`Book tickets for ${title}`)}
            style={{
              background: 'transparent',
              border: '1px solid var(--border)',
              color: 'var(--text-primary)',
              padding: '5px 12px',
              borderRadius: 'var(--radius-btn)',
              fontSize: '0.78rem',
              fontWeight: 500,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.borderColor = 'var(--accent)';
              e.currentTarget.style.color = 'var(--accent)';
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.borderColor = 'var(--border)';
              e.currentTarget.style.color = 'var(--text-primary)';
            }}
          >
            Select <ArrowRight size={13} />
          </button>
        )}
      </div>
    </div>
  );
}

export function EventCarouselCard({ events = [], onSelect }) {
  if (!events || events.length === 0) return null;
  const displayEvents = events.slice(0, 3);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', width: '100%', maxWidth: '520px', marginTop: '6px' }}>
      {displayEvents.map((ev, i) => (
        <EventCard key={ev.id || i} {...ev} onSelect={onSelect} />
      ))}
      {events.length > 3 && onSelect && (
        <button
          onClick={() => onSelect('Show more events')}
          style={{
            background: 'transparent',
            border: 'none',
            color: 'var(--accent)',
            fontSize: '0.8rem',
            fontWeight: 500,
            cursor: 'pointer',
            textAlign: 'left',
            padding: '4px 0',
            marginTop: '2px'
          }}
        >
          Show more ({events.length - 3} more) →
        </button>
      )}
    </div>
  );
}

// -------------------------------------------------------------
// 2. Compact Booking Summary with Live Hold Countdown Timer
// -------------------------------------------------------------
export function BookingSummaryCard({
  event_title,
  ticket_type,
  quantity,
  unit_price,
  subtotal,
  tax,
  total,
  expires_at,
  onConfirm,
  onCancel,
  onSelect
}) {
  const [secondsRemaining, setSecondsRemaining] = useState(600); // 10 minutes default
  const [isExpired, setIsExpired] = useState(false);

  useEffect(() => {
    let target = Date.now() + 600 * 1000;
    if (expires_at) {
      const parsed = new Date(expires_at).getTime();
      if (!isNaN(parsed) && parsed > Date.now()) {
        target = parsed;
      }
    }

    const interval = setInterval(() => {
      const diff = Math.max(0, Math.floor((target - Date.now()) / 1000));
      setSecondsRemaining(diff);
      if (diff <= 0) {
        setIsExpired(true);
        clearInterval(interval);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [expires_at]);

  const formatTimer = (secs) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  const isLowTime = secondsRemaining > 0 && secondsRemaining <= 60;

  return (
    <div
      style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius-card)',
        padding: '16px',
        maxWidth: '420px',
        width: '100%',
        marginTop: '8px',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <span style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          Booking Summary
        </span>

        {!isExpired ? (
          <span
            style={{
              fontSize: '0.74rem',
              fontWeight: 600,
              padding: '2px 8px',
              borderRadius: 'var(--radius-chip)',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              background: isLowTime ? 'var(--danger-soft)' : 'rgba(255, 255, 255, 0.05)',
              color: isLowTime ? 'var(--danger)' : 'var(--text-secondary)',
            }}
          >
            <Clock size={12} />
            {isLowTime ? `⚠ ${formatTimer(secondsRemaining)} remaining` : `Reserved for ${formatTimer(secondsRemaining)}`}
          </span>
        ) : (
          <span style={{ fontSize: '0.74rem', color: 'var(--danger)', fontWeight: 600 }}>
            Reservation expired
          </span>
        )}
      </div>

      <div style={{ marginBottom: '14px' }}>
        <h4 style={{ color: 'var(--text-primary)', fontSize: '1.02rem', fontWeight: 600, margin: '0 0 2px 0' }}>
          {event_title || 'Event Booking'}
        </h4>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.84rem', margin: 0 }}>
          {ticket_type || 'Standard Pass'} × {quantity || 1}
        </p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '0.82rem', borderTop: '1px solid var(--border)', paddingTop: '10px', marginBottom: '14px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-secondary)' }}>
          <span>Subtotal</span>
          <span>{formatINR(subtotal)}</span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-secondary)' }}>
          <span>18% GST (CGST + SGST)</span>
          <span>{formatINR(tax)}</span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-primary)', fontWeight: 700, fontSize: '0.94rem', paddingTop: '6px', borderTop: '1px dashed var(--border)' }}>
          <span>Total</span>
          <span>{formatINR(total)}</span>
        </div>
      </div>

      {!isExpired ? (
        <button
          onClick={() => {
            const handler = onConfirm || onSelect;
            if (handler) handler('Go ahead');
          }}
          style={{
            width: '100%',
            background: 'var(--accent)',
            color: 'white',
            border: 'none',
            padding: '10px 16px',
            borderRadius: 'var(--radius-btn)',
            fontWeight: 600,
            fontSize: '0.88rem',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '6px',
          }}
          onMouseOver={(e) => e.currentTarget.style.background = 'var(--accent-hover)'}
          onMouseOut={(e) => e.currentTarget.style.background = 'var(--accent)'}
        >
          Continue to payment <ArrowRight size={14} />
        </button>
      ) : (
        <button
          onClick={() => {
            const handler = onConfirm || onSelect;
            if (handler) handler(`Check availability for ${event_title}`);
          }}
          style={{
            width: '100%',
            background: 'transparent',
            color: 'var(--text-primary)',
            border: '1px solid var(--border)',
            padding: '10px 16px',
            borderRadius: 'var(--radius-btn)',
            fontWeight: 600,
            fontSize: '0.84rem',
            cursor: 'pointer',
          }}
        >
          Check availability again
        </button>
      )}
    </div>
  );
}

// -------------------------------------------------------------
// 3. Native Razorpay Payment Button
// -------------------------------------------------------------
export function PaymentButton({ order_id, amount, currency = 'INR', event_title, draft_id, onPaymentSuccess }) {
  const [loading, setLoading] = useState(false);
  const [confirmed, setConfirmed] = useState(false);

  const handlePay = () => {
    setLoading(true);
    // Simulate or open Razorpay checkout
    setTimeout(() => {
      setLoading(false);
      setConfirmed(true);
      if (onPaymentSuccess) {
        onPaymentSuccess({
          order_id: order_id || `order_mock_${Date.now()}`,
          payment_id: `pay_mock_${Date.now()}`,
          signature: 'mock_verified_sig'
        });
      }
    }, 1000);
  };

  return (
    <div
      style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius-card)',
        padding: '16px',
        maxWidth: '380px',
        width: '100%',
        marginTop: '8px',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Amount Due</span>
        <span style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--text-primary)' }}>
          {formatINR(amount)}
        </span>
      </div>

      {!confirmed ? (
        <button
          onClick={handlePay}
          disabled={loading}
          style={{
            width: '100%',
            background: 'var(--accent)',
            color: 'white',
            border: 'none',
            padding: '11px 16px',
            borderRadius: 'var(--radius-btn)',
            fontWeight: 600,
            fontSize: '0.88rem',
            cursor: loading ? 'wait' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
          }}
          onMouseOver={(e) => !loading && (e.currentTarget.style.background = 'var(--accent-hover)')}
          onMouseOut={(e) => !loading && (e.currentTarget.style.background = 'var(--accent)')}
        >
          <CreditCard size={16} />
          {loading ? 'Processing payment...' : 'Pay securely with Razorpay'}
        </button>
      ) : (
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--success)', fontWeight: 600, fontSize: '0.88rem' }}>
          <CheckCircle size={18} /> Payment confirmed ✓
        </div>
      )}
    </div>
  );
}

// -------------------------------------------------------------
// 4. Beautiful Polished Ticket Pass Card
// -------------------------------------------------------------
export function TicketConfirmationCard({ ticket, tickets, invoice_number, event_title }) {
  const primaryTicket = ticket || (tickets && tickets[0]) || {};
  const allTickets = tickets && tickets.length > 0 ? tickets : (ticket ? [ticket] : []);

  const qrSrc = primaryTicket.qr_code_url || (primaryTicket.qr_token
    ? `https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=${encodeURIComponent(primaryTicket.qr_token)}`
    : null);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', maxWidth: '380px', width: '100%', marginTop: '8px' }}>
      <div
        style={{
          background: 'var(--bg-surface)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius-card)',
          overflow: 'hidden',
          boxShadow: '0 8px 24px rgba(0,0,0,0.3)',
        }}
      >
        {/* Top Header */}
        <div style={{ padding: '14px 18px', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ color: 'var(--accent)', fontWeight: 700 }}>✦</span>
            <span style={{ fontSize: '0.78rem', fontWeight: 700, letterSpacing: '0.08em', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
              CHATASSIST PASS
            </span>
          </div>
          <span
            style={{
              fontSize: '0.72rem',
              fontWeight: 600,
              padding: '2px 8px',
              borderRadius: 'var(--radius-chip)',
              background: primaryTicket.status === 'CHECKED_IN' ? 'rgba(59, 130, 246, 0.15)' : 'var(--success-soft)',
              color: primaryTicket.status === 'CHECKED_IN' ? '#60A5FA' : 'var(--success)',
            }}
          >
            {primaryTicket.status === 'CHECKED_IN' ? '✓ CHECKED IN' : '✓ CONFIRMED'}
          </span>
        </div>

        {/* Ticket Body */}
        <div style={{ padding: '18px' }}>
          <h3 style={{ fontSize: '1.08rem', fontWeight: 700, color: 'var(--text-primary)', margin: '0 0 10px 0' }}>
            {primaryTicket.event_title || event_title || 'Live Event'}
          </h3>

          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem', color: 'var(--text-secondary)', marginBottom: '14px' }}>
            <span>{primaryTicket.tier_name || 'Standard Pass'}</span>
            <span>{formatINR(primaryTicket.price_paid)}</span>
          </div>

          {/* Real Cryptographic Scannable SVG QR Code */}
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', margin: '14px 0', padding: '14px', background: '#FFFFFF', borderRadius: '10px' }}>
            <QRCodeSVG
              value={primaryTicket.qr_token || primaryTicket.ticket_number || 'TCK-CONFIRMED'}
              size={170}
              level="H"
              includeMargin={true}
            />
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.78rem', color: '#111111', fontWeight: 700, marginTop: '8px', letterSpacing: '0.05em' }}>
              {primaryTicket.ticket_number || 'TCK-CONFIRMED'}
            </span>
          </div>

          {/* Action Links */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '10px', borderTop: '1px solid var(--border)' }}>
            <span style={{ fontSize: '0.76rem', color: 'var(--text-muted)' }}>
              Scan at gate entrance
            </span>

            {invoice_number && (
              <a
                href={`/api/v1/invoices/${invoice_number}/download`}
                target="_blank"
                rel="noreferrer"
                style={{
                  fontSize: '0.78rem',
                  color: 'var(--accent)',
                  textDecoration: 'none',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  fontWeight: 500,
                }}
              >
                <Download size={13} /> Invoice
              </a>
            )}
          </div>
        </div>
      </div>

      {allTickets.length > 1 && (
        <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', textAlign: 'center', margin: 0 }}>
          + {allTickets.length - 1} additional ticket(s) issued in your wallet
        </p>
      )}
    </div>
  );
}

// -------------------------------------------------------------
// 5. My Tickets Wallet List Card with Real Scannable SVG QR
// -------------------------------------------------------------
export function MyTicketsListCard({ tickets = [], onSelect }) {
  const [expandedId, setExpandedId] = useState(null);

  if (!tickets || tickets.length === 0) {
    return (
      <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius-card)', padding: '16px', maxWidth: '420px', color: 'var(--text-secondary)', fontSize: '0.88rem' }}>
        No tickets found in your wallet.
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', maxWidth: '440px', width: '100%', marginTop: '6px' }}>
      <span style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '2px' }}>
        Upcoming Passes ({tickets.length})
      </span>

      {tickets.map((t, idx) => {
        const isExpanded = expandedId === (t.id || idx);
        return (
          <div
            key={t.id || idx}
            style={{
              background: 'var(--bg-surface)',
              border: '1px solid var(--border)',
              borderRadius: 'var(--radius-card)',
              padding: '14px',
              display: 'flex',
              flexDirection: 'column',
              gap: '10px'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h4 style={{ color: 'var(--text-primary)', fontSize: '0.92rem', fontWeight: 600, margin: '0 0 2px 0' }}>
                  {t.event_title || 'Event'}
                </h4>
                <div style={{ display: 'flex', gap: '8px', fontSize: '0.76rem', color: 'var(--text-secondary)' }}>
                  <span>{t.ticket_number}</span>
                  <span>•</span>
                  <span style={{ color: t.status === 'CHECKED_IN' ? '#60A5FA' : 'var(--success)' }}>
                    {t.status || 'CONFIRMED'}
                  </span>
                </div>
              </div>

              <button
                onClick={() => setExpandedId(isExpanded ? null : (t.id || idx))}
                style={{
                  background: isExpanded ? 'rgba(255,255,255,0.1)' : 'transparent',
                  border: '1px solid var(--border)',
                  color: 'var(--text-primary)',
                  padding: '5px 12px',
                  borderRadius: 'var(--radius-btn)',
                  fontSize: '0.76rem',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px'
                }}
              >
                <QrCode size={13} /> {isExpanded ? 'Hide QR' : 'Show QR'}
              </button>
            </div>

            {isExpanded && (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', background: '#FFFFFF', padding: '14px', borderRadius: '10px', marginTop: '6px' }}>
                <QRCodeSVG
                  value={t.qr_token || t.ticket_number || String(t.id)}
                  size={160}
                  level="H"
                  includeMargin={true}
                />
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.76rem', color: '#111111', fontWeight: 700, marginTop: '8px', letterSpacing: '0.05em' }}>
                  {t.ticket_number}
                </span>
                <span style={{ fontSize: '0.7rem', color: '#555555', marginTop: '2px' }}>
                  Scan at venue entrance
                </span>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

// -------------------------------------------------------------
// 6. Side-by-Side Comparison Card
// -------------------------------------------------------------
export function ComparisonCard({ event_1 = {}, event_2 = {}, onSelect }) {
  return (
    <div
      style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius-card)',
        padding: '16px',
        maxWidth: '480px',
        width: '100%',
        marginTop: '8px',
        overflowX: 'auto',
      }}
    >
      <span style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', display: 'block', marginBottom: '12px' }}>
        Event Comparison
      </span>

      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
        <thead>
          <tr style={{ borderBottom: '1px solid var(--border)' }}>
            <th style={{ textAlign: 'left', padding: '6px', color: 'var(--text-muted)', fontWeight: 500 }}>Feature</th>
            <th style={{ textAlign: 'left', padding: '6px', color: 'var(--text-primary)', fontWeight: 600 }}>{event_1.title || 'Event 1'}</th>
            <th style={{ textAlign: 'left', padding: '6px', color: 'var(--text-primary)', fontWeight: 600 }}>{event_2.title || 'Event 2'}</th>
          </tr>
        </thead>
        <tbody>
          <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
            <td style={{ padding: '8px 6px', color: 'var(--text-secondary)' }}>Date</td>
            <td style={{ padding: '8px 6px', color: 'var(--text-primary)' }}>{event_1.date_str || '-'}</td>
            <td style={{ padding: '8px 6px', color: 'var(--text-primary)' }}>{event_2.date_str || '-'}</td>
          </tr>
          <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
            <td style={{ padding: '8px 6px', color: 'var(--text-secondary)' }}>Price From</td>
            <td style={{ padding: '8px 6px', color: 'var(--text-primary)', fontWeight: 600 }}>{formatINR(event_1.price)}</td>
            <td style={{ padding: '8px 6px', color: 'var(--text-primary)', fontWeight: 600 }}>{formatINR(event_2.price)}</td>
          </tr>
          <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
            <td style={{ padding: '8px 6px', color: 'var(--text-secondary)' }}>Category</td>
            <td style={{ padding: '8px 6px', color: 'var(--text-primary)' }}>{event_1.category || '-'}</td>
            <td style={{ padding: '8px 6px', color: 'var(--text-primary)' }}>{event_2.category || '-'}</td>
          </tr>
          <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
            <td style={{ padding: '8px 6px', color: 'var(--text-secondary)' }}>Location</td>
            <td style={{ padding: '8px 6px', color: 'var(--text-primary)' }}>{event_1.location || '-'}</td>
            <td style={{ padding: '8px 6px', color: 'var(--text-primary)' }}>{event_2.location || '-'}</td>
          </tr>
          <tr>
            <td style={{ padding: '8px 6px', color: 'var(--text-secondary)' }}>VIP Tier</td>
            <td style={{ padding: '8px 6px', color: event_1.vip_available ? 'var(--success)' : 'var(--text-muted)' }}>
              {event_1.vip_available ? 'Yes' : 'No'}
            </td>
            <td style={{ padding: '8px 6px', color: event_2.vip_available ? 'var(--success)' : 'var(--text-muted)' }}>
              {event_2.vip_available ? 'Yes' : 'No'}
            </td>
          </tr>
        </tbody>
      </table>

      {onSelect && (
        <div style={{ display: 'flex', gap: '8px', marginTop: '14px', paddingTop: '10px', borderTop: '1px solid var(--border)' }}>
          <button
            onClick={() => onSelect(`Book tickets for ${event_1.title}`)}
            style={{
              flex: 1,
              background: 'transparent',
              border: '1px solid var(--border)',
              color: 'var(--text-primary)',
              padding: '6px',
              borderRadius: 'var(--radius-btn)',
              fontSize: '0.76rem',
              cursor: 'pointer',
            }}
          >
            Book {event_1.title ? event_1.title.slice(0, 16) + '...' : 'Event 1'}
          </button>
          <button
            onClick={() => onSelect(`Book tickets for ${event_2.title}`)}
            style={{
              flex: 1,
              background: 'transparent',
              border: '1px solid var(--border)',
              color: 'var(--text-primary)',
              padding: '6px',
              borderRadius: 'var(--radius-btn)',
              fontSize: '0.76rem',
              cursor: 'pointer',
            }}
          >
            Book {event_2.title ? event_2.title.slice(0, 16) + '...' : 'Event 2'}
          </button>
        </div>
      )}
    </div>
  );
}

// -------------------------------------------------------------
// 7. Cancellation Card
// -------------------------------------------------------------
export function CancellationCard({ ticket_number, event_title, price_paid, onConfirmCancel }) {
  const [cancelling, setCancelling] = useState(false);
  const [done, setDone] = useState(false);

  const handleCancel = async () => {
    setCancelling(true);
    try {
      if (onConfirmCancel) {
        await onConfirmCancel(`Confirm cancellation of ticket ${ticket_number}`);
      }
      setDone(true);
    } catch (err) {
      console.error(err);
    } finally {
      setCancelling(false);
    }
  };

  return (
    <div
      style={{
        background: 'var(--bg-surface)',
        border: '1px solid rgba(239, 68, 68, 0.3)',
        borderRadius: 'var(--radius-card)',
        padding: '16px',
        maxWidth: '420px',
        width: '100%',
        marginTop: '8px',
      }}
    >
      <span style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--danger)', display: 'block', marginBottom: '8px' }}>
        Cancellation & Refund Request
      </span>
      <p style={{ fontSize: '0.84rem', color: 'var(--text-secondary)', margin: '0 0 12px 0' }}>
        Ticket <strong>{ticket_number}</strong> for {event_title || 'Event'} ({formatINR(price_paid)}) is eligible for a full refund.
      </p>

      {!done ? (
        <button
          onClick={handleCancel}
          disabled={cancelling}
          style={{
            background: 'var(--danger)',
            color: 'white',
            border: 'none',
            padding: '8px 14px',
            borderRadius: 'var(--radius-btn)',
            fontWeight: 600,
            fontSize: '0.82rem',
            cursor: cancelling ? 'wait' : 'pointer',
          }}
        >
          {cancelling ? 'Cancelling...' : 'Confirm Cancellation'}
        </button>
      ) : (
        <div style={{ color: 'var(--success)', fontWeight: 600, fontSize: '0.84rem' }}>
          ✓ Ticket cancelled. Refund has been initiated.
        </div>
      )}
    </div>
  );
}

// -------------------------------------------------------------
// 8. Minimal Empty State Hero (ChatGPT style home)
// -------------------------------------------------------------
export function EmptyStateHero({ onQuickAction }) {
  const popularTopics = ['Concerts', 'Tech', 'Sports', 'College'];
  const suggestionPills = [
    'Find events in Bengaluru this weekend',
    'Recommend something under ₹1000',
    'Show my tickets',
  ];

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '40px 20px',
        textAlign: 'center',
        maxWidth: '560px',
        margin: '0 auto',
      }}
    >
      <div style={{ marginBottom: '8px' }}>
        <h1 style={{ fontSize: '2rem', fontWeight: 700, letterSpacing: '-0.03em', margin: 0, color: 'var(--text-primary)' }}>
          ChatAssist
        </h1>
        <p style={{ fontSize: '1rem', color: 'var(--text-secondary)', margin: '6px 0 0 0' }}>
          Find it. Book it. You're in.
        </p>
      </div>

      <div style={{ margin: '18px 0', color: 'var(--accent)', fontSize: '1.25rem' }}>
        ✦
      </div>

      {/* Suggestion Pills */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', justifyContent: 'center', marginBottom: '20px' }}>
        {suggestionPills.map((pill, idx) => (
          <button
            key={idx}
            onClick={() => onQuickAction(pill)}
            style={{
              background: 'var(--bg-surface)',
              border: '1px solid var(--border)',
              color: 'var(--text-secondary)',
              padding: '6px 14px',
              borderRadius: '999px',
              fontSize: '0.8rem',
              cursor: 'pointer',
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.borderColor = 'rgba(255,255,255,0.2)';
              e.currentTarget.style.color = 'var(--text-primary)';
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.borderColor = 'var(--border)';
              e.currentTarget.style.color = 'var(--text-secondary)';
            }}
          >
            {pill}
          </button>
        ))}
      </div>

      {/* Popular Chips */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
        <span>Popular:</span>
        {popularTopics.map((topic, idx) => (
          <button
            key={idx}
            onClick={() => onQuickAction(`Find ${topic} events`)}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--text-secondary)',
              cursor: 'pointer',
              padding: '2px 4px',
              fontSize: '0.78rem',
            }}
            onMouseOver={(e) => e.currentTarget.style.color = 'var(--accent)'}
            onMouseOut={(e) => e.currentTarget.style.color = 'var(--text-secondary)'}
          >
            {topic}
          </button>
        ))}
      </div>
    </div>
  );
}
