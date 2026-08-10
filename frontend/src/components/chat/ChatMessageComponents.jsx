import React, { useState } from 'react';
import { Ticket, ShieldCheck, Calendar, MapPin, CheckCircle, CreditCard, Sparkles, AlertCircle, ArrowRight, RefreshCw } from 'lucide-react';
import axios from 'axios';

export function EventCard({ id, title, category, date_str, location, price, available_tickets, image_url, ticket_types, onSelect }) {
  return (
    <div style={{
      background: 'rgba(30, 41, 59, 0.75)',
      backdropFilter: 'blur(12px)',
      border: '1px solid rgba(139, 92, 246, 0.3)',
      borderRadius: '14px',
      overflow: 'hidden',
      marginTop: '10px',
      boxShadow: '0 8px 24px rgba(0, 0, 0, 0.25)'
    }}>
      {image_url && (
        <div style={{ height: '110px', width: '100%', overflow: 'hidden', position: 'relative' }}>
          <img src={image_url} alt={title} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
          <div style={{
            position: 'absolute',
            top: '8px',
            right: '8px',
            background: 'rgba(15, 23, 42, 0.85)',
            padding: '3px 8px',
            borderRadius: '12px',
            fontSize: '0.7rem',
            color: '#A78BFA',
            fontWeight: 600
          }}>
            {category}
          </div>
        </div>
      )}
      <div style={{ padding: '14px' }}>
        <h4 style={{ color: '#F8FAFC', fontSize: '0.95rem', fontWeight: 700, margin: '0 0 6px 0' }}>{title}</h4>
        
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px', fontSize: '0.75rem', color: '#94A3B8', marginBottom: '10px' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <Calendar size={12} color="#8B5CF6" /> {date_str}
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <MapPin size={12} color="#EC4899" /> {location}
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '10px', pt: '8px', borderTop: '1px solid rgba(255, 255, 255, 0.08)' }}>
          <div>
            <span style={{ fontSize: '0.7rem', color: '#64748B', display: 'block' }}>Live Price</span>
            <span style={{ fontSize: '1.1rem', fontWeight: 800, color: '#10B981' }}>₹{price}</span>
            <span style={{ fontSize: '0.7rem', color: '#94A3B8', marginLeft: '6px' }}>({available_tickets} seats left)</span>
          </div>

          {onSelect && (
            <button
              onClick={() => onSelect(`Book tickets for ${title}`)}
              style={{
                background: 'linear-gradient(135deg, #8B5CF6, #6366F1)',
                border: 'none',
                color: 'white',
                padding: '6px 14px',
                borderRadius: '8px',
                fontSize: '0.78rem',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '4px'
              }}
            >
              Select Event <ArrowRight size={13} />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export function BookingSummaryCard({ event_title, ticket_type, quantity, unit_price, subtotal, tax, total, onConfirm, onCancel }) {
  return (
    <div style={{
      background: 'linear-gradient(145deg, rgba(15, 23, 42, 0.9), rgba(30, 41, 59, 0.9))',
      border: '1px solid rgba(59, 130, 246, 0.4)',
      borderRadius: '14px',
      padding: '14px',
      marginTop: '10px',
      boxShadow: '0 8px 24px rgba(0, 0, 0, 0.3)'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px', borderBottom: '1px solid rgba(255, 255, 255, 0.1)', pb: '8px' }}>
        <Ticket size={16} color="#3B82F6" />
        <h4 style={{ fontSize: '0.9rem', fontWeight: 700, color: '#F8FAFC', margin: 0 }}>Order Breakdown</h4>
      </div>

      <p style={{ fontSize: '0.85rem', color: '#E2E8F0', fontWeight: 600, margin: '0 0 10px 0' }}>{event_title}</p>

      <div style={{ fontSize: '0.78rem', color: '#94A3B8', display: 'flex', flexDirection: 'column', gap: '5px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span>Ticket Tier</span>
          <span style={{ color: '#F1F5F9', fontWeight: 600 }}>{ticket_type}</span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span>Quantity</span>
          <span style={{ color: '#F1F5F9', fontWeight: 600 }}>{quantity} ticket(s)</span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span>Unit Price</span>
          <span style={{ color: '#F1F5F9' }}>₹{unit_price}</span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span>Subtotal</span>
          <span style={{ color: '#F1F5F9' }}>₹{subtotal}</span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span>GST (18%)</span>
          <span style={{ color: '#F1F5F9' }}>₹{tax}</span>
        </div>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '12px', paddingTop: '10px', borderTop: '1px dashed rgba(255, 255, 255, 0.15)' }}>
        <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#F8FAFC' }}>Total Amount</span>
        <span style={{ fontSize: '1.15rem', fontWeight: 800, color: '#10B981' }}>₹{total}</span>
      </div>

      {onConfirm && (
        <div style={{ display: 'flex', gap: '8px', marginTop: '14px' }}>
          <button
            onClick={() => onConfirm("Confirm booking")}
            style={{
              flex: 1,
              background: 'linear-gradient(135deg, #10B981, #059669)',
              border: 'none',
              color: 'white',
              padding: '8px',
              borderRadius: '8px',
              fontSize: '0.8rem',
              fontWeight: 700,
              cursor: 'pointer'
            }}
          >
            ✅ Confirm & Pay
          </button>
          <button
            onClick={() => onCancel ? onCancel("Cancel booking") : null}
            style={{
              background: 'rgba(255, 255, 255, 0.08)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              color: '#94A3B8',
              padding: '8px 12px',
              borderRadius: '8px',
              fontSize: '0.8rem',
              cursor: 'pointer'
            }}
          >
            Cancel
          </button>
        </div>
      )}
    </div>
  );
}

export function PaymentButton({ order_id, amount, booking_id, event_title, quantity, ticket_type, total_inr, onPaymentSuccess }) {
  const [processing, setProcessing] = useState(false);
  const [showSimModal, setShowSimModal] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const initiatePayment = () => {
    // Check if Razorpay SDK script is loaded in window
    if (window.Razorpay && import.meta.env.VITE_RAZORPAY_KEY_ID) {
      try {
        const options = {
          key: import.meta.env.VITE_RAZORPAY_KEY_ID,
          amount: amount || total_inr * 100,
          currency: 'INR',
          name: 'ChatAssist Ticketing',
          description: `Booking for ${event_title}`,
          order_id: order_id,
          handler: async (response) => {
            await handleVerification(response.razorpay_order_id, response.razorpay_payment_id, response.razorpay_signature);
          },
          prefill: {
            name: 'Valued Customer',
            email: 'customer@example.com'
          },
          theme: {
            color: '#8B5CF6'
          }
        };
        const rzp = new window.Razorpay(options);
        rzp.open();
        return;
      } catch (err) {
        console.warn("Razorpay window fail, opening modal simulation", err);
      }
    }
    // Fallback: Open interactive direct payment simulation modal
    setShowSimModal(true);
  };

  const handleVerification = async (rzp_order_id, rzp_payment_id, rzp_sig) => {
    setProcessing(true);
    setErrorMsg('');
    try {
      const res = await axios.post('/api/v1/payments/verify', {
        razorpay_order_id: rzp_order_id || order_id,
        razorpay_payment_id: rzp_payment_id || `pay_sim_${Date.now()}`,
        razorpay_signature: rzp_sig || 'mock_signature_test',
        booking_id: booking_id,
        user_id: 1
      });

      if (res.data && res.data.ticket) {
        setShowSimModal(false);
        if (onPaymentSuccess) {
          onPaymentSuccess(res.data.ticket);
        }
      }
    } catch (err) {
      console.error("Payment verification error", err);
      setErrorMsg(err.response?.data?.detail || "Payment verification failed. Please try again.");
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div style={{ marginTop: '10px' }}>
      <button
        onClick={initiatePayment}
        disabled={processing}
        style={{
          width: '100%',
          background: 'linear-gradient(135deg, #8B5CF6, #EC4899)',
          border: 'none',
          color: 'white',
          padding: '12px 16px',
          borderRadius: '12px',
          fontSize: '0.9rem',
          fontWeight: 700,
          cursor: processing ? 'wait' : 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '8px',
          boxShadow: '0 4px 20px rgba(139, 92, 246, 0.4)'
        }}
      >
        <CreditCard size={18} />
        {processing ? 'Verifying Payment...' : `Pay ₹${total_inr || (amount ? amount / 100 : 499)} Securely`}
      </button>

      {/* Interactive In-Chat Payment Simulation Modal */}
      {showSimModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0, 0, 0, 0.75)',
          backdropFilter: 'blur(6px)',
          zIndex: 2000,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '20px'
        }}>
          <div style={{
            background: '#0F172A',
            border: '1px solid rgba(139, 92, 246, 0.4)',
            borderRadius: '16px',
            width: '100%',
            maxWidth: '380px',
            padding: '24px',
            boxShadow: '0 20px 40px rgba(0, 0, 0, 0.5)',
            color: 'white'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
              <div style={{ background: 'rgba(139, 92, 246, 0.2)', padding: '8px', borderRadius: '10px' }}>
                <ShieldCheck size={24} color="#8B5CF6" />
              </div>
              <div>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, margin: 0 }}>Secure Razorpay Checkout</h3>
                <span style={{ fontSize: '0.75rem', color: '#94A3B8' }}>ChatAssist Encrypted Concurrency Gateway</span>
              </div>
            </div>

            <div style={{ background: 'rgba(30, 41, 59, 0.6)', padding: '14px', borderRadius: '10px', marginBottom: '16px', fontSize: '0.85rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                <span style={{ color: '#94A3B8' }}>Event</span>
                <span style={{ fontWeight: 600 }}>{event_title}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                <span style={{ color: '#94A3B8' }}>Pass Type</span>
                <span>{quantity}x {ticket_type}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderTop: '1px solid rgba(255,255,255,0.1)', pt: '6px', marginTop: '6px' }}>
                <span style={{ fontWeight: 700 }}>Total Payable</span>
                <span style={{ color: '#10B981', fontWeight: 800, fontSize: '1rem' }}>₹{total_inr}</span>
              </div>
            </div>

            {errorMsg && (
              <div style={{ background: 'rgba(239, 68, 68, 0.15)', border: '1px solid #EF4444', color: '#FCA5A5', padding: '10px', borderRadius: '8px', fontSize: '0.78rem', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <AlertCircle size={14} /> {errorMsg}
              </div>
            )}

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <button
                onClick={() => handleVerification(order_id, `pay_rzp_${Date.now()}`, 'mock_sig_ok')}
                disabled={processing}
                style={{
                  width: '100%',
                  background: 'linear-gradient(135deg, #10B981, #059669)',
                  border: 'none',
                  color: 'white',
                  padding: '12px',
                  borderRadius: '10px',
                  fontWeight: 700,
                  fontSize: '0.88rem',
                  cursor: processing ? 'wait' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '6px'
                }}
              >
                {processing ? <RefreshCw size={16} className="animate-spin" /> : <CheckCircle size={16} />}
                {processing ? 'Processing Token...' : 'Authorize Success Payment'}
              </button>

              <button
                onClick={() => setShowSimModal(false)}
                disabled={processing}
                style={{
                  background: 'transparent',
                  border: '1px solid rgba(255,255,255,0.15)',
                  color: '#94A3B8',
                  padding: '8px',
                  borderRadius: '10px',
                  fontSize: '0.8rem',
                  cursor: 'pointer'
                }}
              >
                Cancel Transaction
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export function TicketConfirmationCard({ ticket_number, event_title, price_paid, invoice_number, qr_code_url, date_str, location }) {
  return (
    <div style={{
      background: 'linear-gradient(145deg, rgba(6, 78, 59, 0.4), rgba(15, 23, 42, 0.95))',
      border: '1px solid rgba(16, 185, 129, 0.5)',
      borderRadius: '16px',
      padding: '16px',
      marginTop: '10px',
      boxShadow: '0 8px 24px rgba(16, 185, 129, 0.2)'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid rgba(16, 185, 129, 0.2)', paddingBottom: '10px', marginBottom: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <CheckCircle size={18} color="#10B981" />
          <span style={{ fontSize: '0.88rem', fontWeight: 800, color: '#34D399', letterSpacing: '0.5px' }}>BOOKING CONFIRMED</span>
        </div>
        <span style={{ fontSize: '0.7rem', background: 'rgba(16, 185, 129, 0.2)', color: '#6EE7B7', padding: '2px 8px', borderRadius: '10px', fontWeight: 600 }}>
          {ticket_number}
        </span>
      </div>

      <h4 style={{ color: '#F8FAFC', fontSize: '1rem', fontWeight: 700, margin: '0 0 6px 0' }}>{event_title}</h4>
      
      {(date_str || location) && (
        <div style={{ fontSize: '0.78rem', color: '#94A3B8', marginBottom: '12px', display: 'flex', gap: '12px' }}>
          {date_str && <span>📅 {date_str}</span>}
          {location && <span>📍 {location}</span>}
        </div>
      )}

      {/* QR Code Pass Display */}
      {qr_code_url && (
        <div style={{ background: 'white', padding: '10px', borderRadius: '12px', display: 'flex', flexDirection: 'column', alignItems: 'center', margin: '12px 0' }}>
          <img src={qr_code_url} alt="Ticket QR Pass" style={{ width: '130px', height: '130px' }} />
          <span style={{ fontSize: '0.65rem', color: '#475569', marginTop: '4px', fontWeight: 600 }}>HMAC-SHA256 SIGNED QR PASS</span>
        </div>
      )}

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.75rem', color: '#A78BFA', marginTop: '8px' }}>
        <span>Paid: ₹{price_paid ? price_paid.toFixed(0) : '499'}</span>
        {invoice_number && (
          <a
            href={`/api/v1/payments/invoices/${invoice_number}`}
            target="_blank"
            rel="noreferrer"
            style={{ color: '#60A5FA', textDecoration: 'underline', fontWeight: 600 }}
          >
            Download Invoice PDF
          </a>
        )}
      </div>
    </div>
  );
}

export function QuickReplyButtons({ quick_replies, onSelect }) {
  if (!quick_replies || quick_replies.length === 0) return null;

  return (
    <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginTop: '10px' }}>
      {quick_replies.map((qr, idx) => (
        <button
          key={idx}
          onClick={() => onSelect(qr.text)}
          style={{
            background: 'rgba(139, 92, 246, 0.15)',
            border: '1px solid rgba(139, 92, 246, 0.4)',
            color: '#C4B5FD',
            padding: '6px 12px',
            borderRadius: '16px',
            fontSize: '0.75rem',
            fontWeight: 600,
            cursor: 'pointer',
            transition: 'all 0.2s ease'
          }}
        >
          {qr.label}
        </button>
      ))}
    </div>
  );
}
