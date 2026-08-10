import React, { useState } from 'react';
import { X, Ticket, ShieldCheck, Share2, Check, Download, CreditCard } from 'lucide-react';
import axios from 'axios';

export default function BookingModal({ event, onClose, onBookingSuccess }) {
  const [quantity, setQuantity] = useState(1);
  const [couponCode, setCouponCode] = useState('');
  const [discountAmount, setDiscountAmount] = useState(0);
  const [appliedCoupon, setAppliedCoupon] = useState(null);
  const [couponError, setCouponError] = useState('');
  const [loading, setLoading] = useState(false);
  const [bookingResult, setBookingResult] = useState(null);
  const [copiedShare, setCopiedShare] = useState(false);

  if (!event) return null;

  const rawTotal = event.price * quantity;
  const totalAmount = Math.max(0, rawTotal - discountAmount);

  const handleApplyCoupon = async () => {
    if (!couponCode.trim()) return;
    setCouponError('');
    try {
      const res = await axios.post('/api/v1/coupons/validate', {
        code: couponCode,
        total_amount: rawTotal
      });
      setDiscountAmount(res.data.discount_amount);
      setAppliedCoupon(res.data.code);
    } catch (err) {
      setCouponError(err.response?.data?.detail || 'Invalid promo coupon');
      setDiscountAmount(0);
      setAppliedCoupon(null);
    }
  };


  const handleBook = async () => {
    setLoading(true);
    const idempotencyKey = `KEY-${Date.now()}-${Math.random().toString(36).substring(7)}`;

    try {
      const res = await axios.post('/api/v1/book', {
        event_id: event.id,
        quantity: quantity,
        idempotency_key: idempotencyKey
      });
      setBookingResult(res.data);
      if (onBookingSuccess) onBookingSuccess(res.data);
    } catch (err) {
      alert(err.response?.data?.detail || 'Booking failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleCopyShareLink = () => {
    navigator.clipboard.writeText(`https://chatassist.app/pay-split?event=${event.id}&inviter=Ajay`);
    setCopiedShare(true);
    setTimeout(() => setCopiedShare(false), 2000);
  };

  return (
    <div style={{ position: 'fixed', inset: 0, zIndex: 2000, background: 'rgba(0, 0, 0, 0.75)', backdropFilter: 'blur(8px)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '16px' }}>
      <div className="glass-panel" style={{ width: '100%', maxWidth: '480px', padding: '24px', borderRadius: '20px' }}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'white' }}>
            {bookingResult ? 'Booking Confirmed!' : 'Complete Your Booking'}
          </h2>
          <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
            <X size={20} />
          </button>
        </div>

        {!bookingResult ? (
          <div>
            {/* Event Summary */}
            <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-glass)', padding: '16px', borderRadius: '12px', marginBottom: '20px' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#60A5FA', marginBottom: '4px' }}>{event.title}</h3>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{event.location} • {event.date_str}</p>
            </div>

            {/* Quantity Selector */}
            <div style={{ marginBottom: '20px' }}>
              <label style={{ fontSize: '0.85rem', color: 'var(--text-muted)', display: 'block', marginBottom: '8px' }}>Select Number of Tickets</label>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <button 
                  onClick={() => setQuantity(Math.max(1, quantity - 1))}
                  style={{ background: 'rgba(255,255,255,0.1)', border: 'none', color: 'white', width: '36px', height: '36px', borderRadius: '8px', cursor: 'pointer', fontWeight: 700 }}
                >
                  -
                </button>
                <span style={{ fontSize: '1.25rem', fontWeight: 800, color: 'white', width: '40px', textAlign: 'center' }}>{quantity}</span>
                <button 
                  onClick={() => setQuantity(Math.min(event.available_tickets, quantity + 1))}
                  style={{ background: 'rgba(255,255,255,0.1)', border: 'none', color: 'white', width: '36px', height: '36px', borderRadius: '8px', cursor: 'pointer', fontWeight: 700 }}
                >
                  +
                </button>
              </div>
            </div>

            {/* Coupon Code Section */}
            <div style={{ marginBottom: '20px' }}>
              <label style={{ fontSize: '0.85rem', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>Have a Promo Coupon? (Try WELCOME10 or TECH500)</label>
              <div style={{ display: 'flex', gap: '8px' }}>
                <input
                  type="text"
                  placeholder="e.g. WELCOME10"
                  value={couponCode}
                  onChange={(e) => setCouponCode(e.target.value.toUpperCase())}
                  style={{ flex: 1, background: 'rgba(15, 23, 42, 0.6)', border: '1px solid var(--border-glass)', borderRadius: '8px', padding: '8px 12px', color: 'white', fontSize: '0.875rem', outline: 'none' }}
                />
                <button
                  type="button"
                  onClick={handleApplyCoupon}
                  style={{ background: 'rgba(59, 130, 246, 0.2)', border: '1px solid rgba(59, 130, 246, 0.4)', color: '#60A5FA', padding: '8px 14px', borderRadius: '8px', cursor: 'pointer', fontWeight: 600, fontSize: '0.85rem' }}
                >
                  Apply Code
                </button>
              </div>
              {appliedCoupon && <span style={{ fontSize: '0.75rem', color: '#34D399', marginTop: '4px', display: 'block' }}>✓ Promo '{appliedCoupon}' Applied (-₹{discountAmount.toFixed(2)})</span>}
              {couponError && <span style={{ fontSize: '0.75rem', color: '#F87171', marginTop: '4px', display: 'block' }}>{couponError}</span>}
            </div>

            {/* Price Breakdown */}
            <div style={{ borderTop: '1px solid var(--border-glass)', paddingTop: '16px', marginBottom: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '6px' }}>
                <span>Subtotal ({quantity}x ₹{event.price})</span>
                <span>₹{rawTotal.toFixed(2)}</span>
              </div>
              {discountAmount > 0 && (
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem', color: '#34D399', marginBottom: '6px' }}>
                  <span>Promo Discount ({appliedCoupon})</span>
                  <span>-₹{discountAmount.toFixed(2)}</span>
                </div>
              )}
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '1.25rem', fontWeight: 800, color: 'white' }}>
                <span>Total Amount</span>
                <span className="gradient-text">₹{totalAmount.toFixed(2)}</span>
              </div>
            </div>


            {/* Split Payment Share Link */}
            <div style={{ marginBottom: '20px', background: 'rgba(139, 92, 246, 0.1)', border: '1px border-purple-500', padding: '12px', borderRadius: '10px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '0.75rem', color: '#C084FC' }}>Group booking? Split payment link:</span>
              <button 
                onClick={handleCopyShareLink}
                style={{ background: 'rgba(139, 92, 246, 0.3)', border: 'none', color: 'white', padding: '4px 8px', borderRadius: '6px', fontSize: '0.75rem', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px' }}
              >
                {copiedShare ? <Check size={12} /> : <Share2 size={12} />} {copiedShare ? 'Copied!' : 'Copy Share Link'}
              </button>
            </div>

            {/* Submit Button */}
            <button
              onClick={handleBook}
              disabled={loading}
              className="gradient-btn"
              style={{ width: '100%', padding: '14px', justifyContent: 'center', borderRadius: '12px', fontSize: '1rem' }}
            >
              <CreditCard size={18} /> {loading ? 'Securing Seat & Generating Ticket...' : `Pay ₹${totalAmount.toFixed(0)} Now`}
            </button>
          </div>
        ) : (
          /* Confirmation State */
          <div style={{ textAlign: 'center', padding: '10px 0' }}>
            <div style={{ background: 'rgba(16, 185, 129, 0.2)', width: '64px', height: '64px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px auto', border: '1px solid rgba(16, 185, 129, 0.4)' }}>
              <ShieldCheck size={36} color="#34D399" />
            </div>

            <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'white', marginBottom: '4px' }}>Ticket Secured!</h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '16px' }}>Your reservation is confirmed in our database.</p>

            <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-glass)', padding: '16px', borderRadius: '12px', textAlign: 'left', marginBottom: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Ticket Number</span>
                <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#60A5FA' }}>{bookingResult.ticket_number}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>GST Invoice No.</span>
                <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'white' }}>{bookingResult.invoice_number}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Amount Paid</span>
                <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#34D399' }}>₹{bookingResult.price_paid}</span>
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <a 
                href={`https://pay.google.com/gp/v/save/chatassist_ticket_${bookingResult.ticket_id}`}
                target="_blank" 
                rel="noreferrer" 
                style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
                  background: 'linear-gradient(135deg, #1a73e8 0%, #00e676 100%)',
                  color: 'white', padding: '12px', borderRadius: '10px', fontWeight: 700,
                  fontSize: '0.875rem', textDecoration: 'none', boxShadow: '0 4px 12px rgba(26, 115, 232, 0.3)'
                }}
              >
                <Wallet size={16} /> Add to Google Wallet Pass
              </a>

              <div style={{ display: 'flex', gap: '12px' }}>
                <a 
                  href={`/api/v1/invoices/${bookingResult.invoice_number}`} 
                  target="_blank" 
                  rel="noreferrer" 
                  className="gradient-btn"
                  style={{ flex: 1, textDecoration: 'none', justifyContent: 'center', padding: '12px', fontSize: '0.875rem' }}
                >
                  <Download size={16} /> GST Tax Invoice
                </a>

                <button 
                  onClick={onClose} 
                  style={{ flex: 1, background: 'rgba(255,255,255,0.1)', border: '1px solid var(--border-glass)', color: 'white', borderRadius: '10px', cursor: 'pointer', fontWeight: 600 }}
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

