import React, { useState, useEffect } from 'react';
import { X, Ticket, ShieldCheck, Share2, Check, Download, CreditCard, Wallet } from 'lucide-react';
import axios from 'axios';

export default function BookingModal({ event, onClose, onBookingSuccess }) {
  const [tiers, setTiers] = useState([]);
  const [selectedTier, setSelectedTier] = useState(null);
  const [quantity, setQuantity] = useState(1);
  const [couponCode, setCouponCode] = useState('');
  const [discountAmount, setDiscountAmount] = useState(0);
  const [appliedCoupon, setAppliedCoupon] = useState(null);
  const [couponError, setCouponError] = useState('');
  const [loading, setLoading] = useState(false);
  const [bookingResult, setBookingResult] = useState(null);
  const [copiedShare, setCopiedShare] = useState(false);
  const [bookingError, setBookingError] = useState('');

  // Fetch real-time ticket tier inventory from backend
  useEffect(() => {
    if (event?.id) {
      axios.get(`/api/v1/events/${event.id}/tiers`)
        .then(res => {
          const tierList = res.data?.tiers || [];
          setTiers(tierList);
          if (tierList.length > 0) {
            const defaultSelected = tierList.find(t => t.available_quantity > 0) || tierList[0];
            setSelectedTier(defaultSelected);
            setQuantity(Math.max(1, defaultSelected.min_per_order || 1));
          }
        })
        .catch(err => console.error("Failed to fetch event tiers:", err));
    }
  }, [event?.id]);

  if (!event) return null;

  const currentPrice = selectedTier ? selectedTier.price : (event.price || 0);
  const rawTotal = currentPrice * quantity;
  const totalAmount = Math.max(0, rawTotal - discountAmount);
  const maxAllowedQty = selectedTier 
    ? Math.min(selectedTier.max_per_order || 10, selectedTier.available_quantity || 0)
    : (event.available_tickets || 10);
  const minAllowedQty = selectedTier ? (selectedTier.min_per_order || 1) : 1;

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
    setBookingError('');
    const idempotencyKey = `KEY-${Date.now()}-${Math.random().toString(36).substring(7)}`;

    try {
      const res = await axios.post('/api/v1/book', {
        event_id: event.id,
        quantity: quantity,
        ticket_type: selectedTier ? selectedTier.name : 'General Admission',
        tier_id: selectedTier ? selectedTier.id : null,
        idempotency_key: idempotencyKey
      });
      setBookingResult(res.data);
      if (onBookingSuccess) onBookingSuccess(res.data);
    } catch (err) {
      const detail = err.response?.data?.detail;
      const errorMsg = typeof detail === 'object' && detail?.message 
        ? detail.message 
        : (detail || "⚠️ We couldn't reserve your tickets right now.");
      setBookingError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleCopyShareLink = () => {
    navigator.clipboard.writeText(`https://chatassist.app/pay-split?event=${event.id}&inviter=Customer`);
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
            <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-glass)', padding: '16px', borderRadius: '12px', marginBottom: '16px' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#60A5FA', marginBottom: '4px' }}>{event.title}</h3>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{event.location} • {event.date_str}</p>
            </div>

            {/* Ticket Tier Selection */}
            {tiers.length > 0 && (
              <div style={{ marginBottom: '18px' }}>
                <label style={{ fontSize: '0.85rem', color: 'var(--text-muted)', display: 'block', marginBottom: '8px', fontWeight: 600 }}>
                  Select Ticket Tier
                </label>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {tiers.map(t => {
                    const isSelected = selectedTier?.id === t.id;
                    const isSoldOut = t.available_quantity <= 0;
                    return (
                      <div
                        key={t.id}
                        onClick={() => {
                          if (!isSoldOut) {
                            setSelectedTier(t);
                            setQuantity(Math.max(t.min_per_order || 1, 1));
                          }
                        }}
                        style={{
                          background: isSelected ? 'rgba(59, 130, 246, 0.15)' : 'rgba(255, 255, 255, 0.03)',
                          border: isSelected ? '1.5px solid #3B82F6' : '1px solid var(--border-glass)',
                          borderRadius: '10px',
                          padding: '10px 14px',
                          display: 'flex',
                          alignItems: 'center',
                          justify: 'space-between',
                          cursor: isSoldOut ? 'not-allowed' : 'pointer',
                          opacity: isSoldOut ? 0.5 : 1,
                          transition: 'all 0.2s'
                        }}
                      >
                        <div>
                          <span style={{ fontSize: '0.9rem', fontWeight: 700, color: isSelected ? '#60A5FA' : 'white', display: 'block' }}>
                            {t.name}
                          </span>
                          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                            Limit: {t.min_per_order}-{t.max_per_order} per order
                          </span>
                        </div>
                        <div style={{ textAlign: 'right' }}>
                          <span style={{ fontSize: '0.95rem', fontWeight: 800, color: '#34D399', display: 'block' }}>
                            ₹{t.price}
                          </span>
                          <span style={{ fontSize: '0.7rem', fontWeight: 700, color: isSoldOut ? '#F87171' : t.available_quantity <= 5 ? '#F59E0B' : '#34D399' }}>
                            {isSoldOut ? 'SOLD OUT' : `${t.available_quantity} left`}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Booking Error Banner */}
            {bookingError && (
              <div style={{
                background: 'rgba(239, 68, 68, 0.15)',
                border: '1px solid rgba(239, 68, 68, 0.4)',
                borderRadius: '10px',
                padding: '12px 14px',
                marginBottom: '16px',
                fontSize: '0.85rem',
                color: '#F87171',
                lineHeight: 1.4
              }}>
                {bookingError}
              </div>
            )}

            {/* Quantity Selector */}
            <div style={{ marginBottom: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <label style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Select Number of Tickets</label>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  (Max allowed: {maxAllowedQty})
                </span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <button 
                  type="button"
                  onClick={() => setQuantity(Math.max(minAllowedQty, quantity - 1))}
                  disabled={quantity <= minAllowedQty}
                  style={{ background: 'rgba(255,255,255,0.1)', border: 'none', color: 'white', width: '36px', height: '36px', borderRadius: '8px', cursor: quantity <= minAllowedQty ? 'not-allowed' : 'pointer', fontWeight: 700 }}
                >
                  -
                </button>
                <span style={{ fontSize: '1.25rem', fontWeight: 800, color: 'white', width: '40px', textAlign: 'center' }}>{quantity}</span>
                <button 
                  type="button"
                  onClick={() => setQuantity(Math.min(maxAllowedQty, quantity + 1))}
                  disabled={quantity >= maxAllowedQty || maxAllowedQty === 0}
                  style={{ background: 'rgba(255,255,255,0.1)', border: 'none', color: 'white', width: '36px', height: '36px', borderRadius: '8px', cursor: (quantity >= maxAllowedQty || maxAllowedQty === 0) ? 'not-allowed' : 'pointer', fontWeight: 700 }}
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
              <CreditCard size={18} /> {loading ? 'Preparing secure checkout...' : `Pay ₹${totalAmount.toFixed(0)} Now`}
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

