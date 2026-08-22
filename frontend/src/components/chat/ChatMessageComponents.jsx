import React, { useState } from 'react';
import { Ticket, ShieldCheck, Calendar, MapPin, CheckCircle, CreditCard, Sparkles, AlertCircle, ArrowRight, RefreshCw, Wallet, Send, Plus, Minus } from 'lucide-react';
import axios from 'axios';

export function formatINR(val) {
  if (val === undefined || val === null || isNaN(val)) return '₹0.00';
  return Number(val).toLocaleString('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  });
}

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

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '10px', paddingTop: '8px', borderTop: '1px solid rgba(255, 255, 255, 0.08)' }}>
          <div>
            <span style={{ fontSize: '0.7rem', color: '#64748B', display: 'block' }}>From</span>
            <span style={{ fontSize: '1.1rem', fontWeight: 800, color: '#10B981' }}>{formatINR(price)}</span>
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

export function BookingSummaryCard({
  event_title,
  ticket_type,
  quantity,
  unit_price,
  subtotal,
  tax,
  total,
  available_seats,
  available_tickets,
  seats_available,
  max_tickets_per_booking,
  maxTicketsPerBooking,
  effective_max,
  onConfirm,
  onCancel,
  onSelect
}) {
  const currentQty = Number(quantity ?? 1);

  const availableSeats = Number(
    available_seats ?? available_tickets ?? seats_available ?? 0
  );

  const configuredMax = Number(
    max_tickets_per_booking ?? maxTicketsPerBooking ?? 10
  );

  const effectiveMax = Number(
    effective_max ?? (
      Math.max(
        1,
        Math.min(
          configuredMax,
          availableSeats > 0 ? availableSeats : configuredMax
        )
      )
    )
  );

  const handleQtyChange = (newQty) => {
    if (newQty < 1 || newQty > effectiveMax) return;
    const selectHandler = onSelect || onConfirm;
    if (selectHandler) {
      selectHandler(`${newQty} ${ticket_type || 'Standard'} tickets`);
    }
  };

  const handleTierSelect = (tierName) => {
    const selectHandler = onSelect || onConfirm;
    if (selectHandler) {
      selectHandler(`${currentQty} ${tierName} tickets`);
    }
  };

  const isMaxReached = currentQty >= effectiveMax;

  return (
    <div style={{
      background: 'linear-gradient(145deg, rgba(15, 23, 42, 0.9), rgba(30, 41, 59, 0.9))',
      border: '1px solid rgba(59, 130, 246, 0.4)',
      borderRadius: '14px',
      padding: '14px',
      marginTop: '10px',
      boxShadow: '0 8px 24px rgba(0, 0, 0, 0.3)'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px', borderBottom: '1px solid rgba(255, 255, 255, 0.1)', paddingBottom: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Ticket size={16} color="#3B82F6" />
          <h4 style={{ fontSize: '0.9rem', fontWeight: 700, color: '#F8FAFC', margin: 0 }}>Booking Summary</h4>
        </div>
        <span style={{ fontSize: '0.7rem', color: '#FDE047', background: 'rgba(234, 179, 8, 0.15)', padding: '2px 8px', borderRadius: '10px', fontWeight: 600 }}>
          ⏱️ Seats held 10m
        </span>
      </div>

      <p style={{ fontSize: '0.88rem', color: '#E2E8F0', fontWeight: 700, margin: '0 0 10px 0' }}>{event_title}</p>

      {/* Tier Selector */}
      <div style={{ marginBottom: '12px' }}>
        <label style={{ fontSize: '0.72rem', color: '#94A3B8', display: 'block', marginBottom: '6px', fontWeight: 600 }}>Ticket Tier</label>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            type="button"
            onClick={() => handleTierSelect('Standard')}
            style={{
              flex: 1,
              padding: '6px 8px',
              borderRadius: '8px',
              border: (ticket_type || 'Standard').toLowerCase().includes('standard') ? '1px solid #8B5CF6' : '1px solid rgba(255,255,255,0.1)',
              background: (ticket_type || 'Standard').toLowerCase().includes('standard') ? 'rgba(139, 92, 246, 0.25)' : 'rgba(255,255,255,0.05)',
              color: 'white',
              fontSize: '0.75rem',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            Standard
          </button>
          <button
            type="button"
            onClick={() => handleTierSelect('VIP Pass')}
            style={{
              flex: 1,
              padding: '6px 8px',
              borderRadius: '8px',
              border: (ticket_type || '').toLowerCase().includes('vip') ? '1px solid #EC4899' : '1px solid rgba(255,255,255,0.1)',
              background: (ticket_type || '').toLowerCase().includes('vip') ? 'rgba(236, 72, 153, 0.25)' : 'rgba(255,255,255,0.05)',
              color: 'white',
              fontSize: '0.75rem',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            VIP Pass
          </button>
        </div>
      </div>

      {/* Quantity Stepper */}
      <div style={{ marginBottom: '12px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(15, 23, 42, 0.5)', padding: '8px 12px', borderRadius: '8px' }}>
          <span style={{ fontSize: '0.75rem', color: '#94A3B8', fontWeight: 600 }}>Quantity</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <button
              type="button"
              onClick={() => handleQtyChange(currentQty - 1)}
              disabled={currentQty <= 1}
              style={{
                background: 'rgba(255, 255, 255, 0.1)',
                border: 'none',
                color: 'white',
                width: '24px',
                height: '24px',
                borderRadius: '6px',
                cursor: currentQty <= 1 ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                opacity: currentQty <= 1 ? 0.4 : 1
              }}
            >
              <Minus size={12} />
            </button>
            <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'white', minWidth: '16px', textAlign: 'center' }}>
              {currentQty}
            </span>
            <button
              type="button"
              onClick={() => handleQtyChange(currentQty + 1)}
              disabled={isMaxReached}
              style={{
                background: isMaxReached ? 'rgba(255, 255, 255, 0.05)' : 'rgba(255, 255, 255, 0.1)',
                border: 'none',
                color: 'white',
                width: '24px',
                height: '24px',
                borderRadius: '6px',
                cursor: isMaxReached ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                opacity: isMaxReached ? 0.4 : 1
              }}
            >
              <Plus size={12} />
            </button>
          </div>
        </div>
        <span style={{ fontSize: '0.68rem', color: '#64748B', display: 'block', marginTop: '4px', textAlign: 'right' }}>
          Available: {availableSeats > 0 ? availableSeats : (available_tickets || '400+')} • Max per booking: {effectiveMax}
        </span>
      </div>

      {/* Breakdown Details */}
      <div style={{ fontSize: '0.78rem', color: '#94A3B8', display: 'flex', flexDirection: 'column', gap: '5px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span>Unit Price</span>
          <span style={{ color: '#F1F5F9' }}>{formatINR(unit_price)}</span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span>Subtotal</span>
          <span style={{ color: '#F1F5F9' }}>{formatINR(subtotal)}</span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span>GST (18%)</span>
          <span style={{ color: '#F1F5F9' }}>{formatINR(tax)}</span>
        </div>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '12px', paddingTop: '10px', borderTop: '1px dashed rgba(255, 255, 255, 0.15)' }}>
        <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#F8FAFC' }}>Total</span>
        <span style={{ fontSize: '1.15rem', fontWeight: 800, color: '#10B981' }}>{formatINR(total)}</span>
      </div>

      {onConfirm && (
        <div style={{ display: 'flex', gap: '8px', marginTop: '14px' }}>
          <button
            type="button"
            onClick={() => onConfirm("Confirm booking")}
            style={{
              flex: 1,
              background: 'linear-gradient(135deg, #10B981, #059669)',
              border: 'none',
              color: 'white',
              padding: '10px',
              borderRadius: '8px',
              fontSize: '0.82rem',
              fontWeight: 700,
              cursor: 'pointer'
            }}
          >
            ✅ Confirm & Pay
          </button>
          <button
            type="button"
            onClick={() => onCancel ? onCancel("Cancel booking") : null}
            style={{
              background: 'rgba(255, 255, 255, 0.08)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              color: '#94A3B8',
              padding: '10px 14px',
              borderRadius: '8px',
              fontSize: '0.82rem',
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
    if (window.Razorpay && import.meta.env.VITE_RAZORPAY_KEY_ID) {
      try {
        const options = {
          key: import.meta.env.VITE_RAZORPAY_KEY_ID,
          amount: amount || Math.round((total_inr || 499) * 100),
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
        {processing ? 'Verifying Payment...' : `✅ Pay ${formatINR(total_inr || (amount ? amount / 100 : 499))}`}
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
                <span style={{ fontSize: '0.75rem', color: '#94A3B8' }}>ChatAssist Gateway</span>
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
              <div style={{ display: 'flex', justifyContent: 'space-between', borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '6px', marginTop: '6px' }}>
                <span style={{ fontWeight: 700 }}>Total Payable</span>
                <span style={{ color: '#10B981', fontWeight: 800, fontSize: '1rem' }}>{formatINR(total_inr)}</span>
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

export function TicketConfirmationCard({ ticket_id, ticket_number, event_title, price_paid, invoice_number, qr_code_url, date_str, location }) {
  const [showTransfer, setShowTransfer] = useState(false);
  const [recipientEmail, setRecipientEmail] = useState('');
  const [transferMsg, setTransferMsg] = useState('');
  const [transferLoading, setTransferLoading] = useState(false);

  const handleTransfer = async () => {
    if (!recipientEmail) return;
    setTransferLoading(true);
    setTransferMsg('');
    try {
      const res = await axios.post(`/api/v1/tickets/${ticket_id || 1}/transfer`, {
        recipient_email: recipientEmail
      });
      setTransferMsg(res.data.message || 'Ticket transferred successfully!');
    } catch (err) {
      setTransferMsg(err.response?.data?.detail || 'Failed to transfer ticket.');
    } finally {
      setTransferLoading(false);
    }
  };

  return (
    <div className="ticket-stub" style={{
      padding: '18px',
      marginTop: '12px',
      animation: 'ticketStamp 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275)'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <CheckCircle size={18} color="var(--gold)" />
          <span className="font-display-title" style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--gold)', letterSpacing: '0.05em' }}>
            BOOKING CONFIRMED
          </span>
        </div>
        <span className="badge badge-gold font-mono-data">
          {ticket_number}
        </span>
      </div>

      <h4 className="font-display-title" style={{ color: 'var(--paper)', fontSize: '1.2rem', fontWeight: 800, margin: '0 0 6px 0' }}>
        {event_title}
      </h4>
      
      {(date_str || location) && (
        <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '12px', display: 'flex', gap: '12px' }}>
          {date_str && <span>📅 {date_str}</span>}
          {location && <span>📍 {location}</span>}
        </div>
      )}

      {/* QR Code Pass Display */}
      {qr_code_url && (
        <div style={{ background: 'white', padding: '12px', borderRadius: '12px', display: 'flex', flexDirection: 'column', alignItems: 'center', margin: '12px 0', boxShadow: '0 4px 12px rgba(0,0,0,0.3)' }}>
          <img src={qr_code_url} alt={`QR Pass for ${ticket_number}`} style={{ width: '140px', height: '140px' }} />
          <span className="font-mono-data" style={{ fontSize: '0.65rem', color: '#151316', marginTop: '6px', fontWeight: 800, letterSpacing: '0.5px' }}>
            HMAC-SHA256 SIGNED QR PASS
          </span>
        </div>
      )}

      <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
        <a 
          href={`https://pay.google.com/gp/v/save/chatassist_ticket_${ticket_id || ticket_number}`}
          target="_blank" 
          rel="noreferrer" 
          style={{
            flex: 1,
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px',
            background: 'linear-gradient(135deg, #1a73e8 0%, #00e676 100%)',
            color: 'white', padding: '8px 12px', borderRadius: '8px', fontWeight: 700,
            fontSize: '0.75rem', textDecoration: 'none', boxShadow: '0 2px 8px rgba(26, 115, 232, 0.3)'
          }}
        >
          <Wallet size={14} /> Save to Google Wallet
        </a>

        <button
          onClick={() => setShowTransfer(!showTransfer)}
          style={{
            flex: 1,
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px',
            background: 'rgba(139, 92, 246, 0.25)',
            border: '1px solid rgba(139, 92, 246, 0.5)',
            color: '#C4B5FD', padding: '8px 12px', borderRadius: '8px', fontWeight: 700,
            fontSize: '0.75rem', cursor: 'pointer'
          }}
        >
          <Send size={14} /> Transfer Ticket
        </button>
      </div>

      {showTransfer && (
        <div style={{ background: 'rgba(15, 23, 42, 0.95)', border: '1px solid rgba(139, 92, 246, 0.4)', padding: '12px', borderRadius: '10px', marginBottom: '12px' }}>
          <span style={{ fontSize: '0.78rem', fontWeight: 700, color: 'white', display: 'block', marginBottom: '6px' }}>
            🎁 Gift / Transfer Ticket to Friend
          </span>
          <p style={{ fontSize: '0.7rem', color: '#94A3B8', margin: '0 0 8px 0' }}>
            Enter recipient's email. Note: Re-signs HMAC token.
          </p>

          {transferMsg && (
            <div style={{ fontSize: '0.75rem', color: transferMsg.includes('successfully') ? '#34D399' : '#FCA5A5', marginBottom: '8px', fontWeight: 600 }}>
              {transferMsg}
            </div>
          )}

          <div style={{ display: 'flex', gap: '6px' }}>
            <input
              type="email"
              placeholder="friend@example.com"
              value={recipientEmail}
              onChange={(e) => setRecipientEmail(e.target.value)}
              style={{
                flex: 1, background: 'rgba(255, 255, 255, 0.08)', border: '1px solid rgba(255, 255, 255, 0.2)',
                color: 'white', borderRadius: '6px', padding: '6px 10px', fontSize: '0.78rem'
              }}
            />
            <button
              onClick={handleTransfer}
              disabled={transferLoading}
              style={{
                background: 'linear-gradient(135deg, #8B5CF6, #6366F1)', border: 'none',
                color: 'white', borderRadius: '6px', padding: '6px 12px', fontSize: '0.78rem', fontWeight: 700, cursor: 'pointer'
              }}
            >
              {transferLoading ? 'Transferring...' : 'Send Transfer'}
            </button>
          </div>
        </div>
      )}

      <div className="ticket-seam" />

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.8rem', color: 'var(--paper)' }}>
        <span>Paid: <strong className="font-mono-data" style={{ color: 'var(--gold)' }}>{formatINR(price_paid || 499)}</strong></span>
        {invoice_number && (
          <a
            href={`/api/v1/invoices/${invoice_number}`}
            target="_blank"
            rel="noreferrer"
            style={{ color: 'var(--gold)', textDecoration: 'underline', fontWeight: 600 }}
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

export function EventCarouselCard({ events, onSelectEvent }) {
  if (!events || events.length === 0) return null;
  return (
    <div style={{
      display: 'flex',
      gap: '12px',
      overflowX: 'auto',
      paddingBottom: '8px',
      marginTop: '12px',
      scrollBehavior: 'smooth'
    }}>
      {events.map((ev, idx) => (
        <div key={ev.id || idx} style={{
          minWidth: '240px',
          maxWidth: '260px',
          background: 'linear-gradient(145deg, rgba(30, 41, 59, 0.9), rgba(15, 23, 42, 0.9))',
          border: '1px solid rgba(139, 92, 246, 0.3)',
          borderRadius: '12px',
          padding: '12px',
          flexShrink: 0,
          boxShadow: '0 4px 16px rgba(0,0,0,0.3)'
        }}>
          <div style={{ fontSize: '0.7rem', color: '#A78BFA', fontWeight: 600, textTransform: 'uppercase', marginBottom: '4px' }}>
            {ev.category || 'Event'}
          </div>
          <h4 style={{ color: '#F8FAFC', fontSize: '0.9rem', fontWeight: 700, margin: '0 0 6px 0', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {ev.title}
          </h4>
          <div style={{ fontSize: '0.75rem', color: '#94A3B8', marginBottom: '8px', display: 'flex', flexDirection: 'column', gap: '3px' }}>
            <span>📅 {ev.date_str || 'Upcoming'}</span>
            <span>📍 {ev.location || 'Bengaluru'}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '10px', paddingTop: '8px', borderTop: '1px solid rgba(255,255,255,0.08)' }}>
            <div>
              <span style={{ fontSize: '0.65rem', color: '#64748B', display: 'block' }}>From</span>
              <span style={{ fontSize: '1rem', fontWeight: 800, color: '#10B981' }}>{formatINR(ev.price)}</span>
            </div>
            <button
              onClick={() => onSelectEvent && onSelectEvent(`Book tickets for ${ev.title}`)}
              style={{
                background: 'linear-gradient(135deg, #8B5CF6, #6366F1)',
                border: 'none',
                color: 'white',
                padding: '6px 12px',
                borderRadius: '8px',
                fontSize: '0.75rem',
                fontWeight: 700,
                cursor: 'pointer'
              }}
            >
              Book Now
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}

export function MyTicketsListCard({ tickets, onSelectTicket }) {
  if (!tickets || tickets.length === 0) return null;
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginTop: '10px' }}>
      {tickets.map((t, idx) => (
        <div key={idx} style={{
          background: 'rgba(30, 41, 59, 0.8)',
          border: '1px solid rgba(139, 92, 246, 0.3)',
          borderRadius: '12px',
          padding: '12px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <div>
            <span style={{ fontSize: '0.7rem', color: '#A78BFA', fontWeight: 600 }}>{t.ticket_number}</span>
            <h4 style={{ margin: '2px 0', fontSize: '0.9rem', color: 'white' }}>{t.event_title}</h4>
            <span style={{ fontSize: '0.75rem', color: '#94A3B8' }}>{t.date_str} • {t.location}</span>
          </div>
          <div style={{ textAlign: 'right' }}>
            <span style={{ fontSize: '0.9rem', fontWeight: 700, color: '#10B981', display: 'block' }}>{formatINR(t.price_paid)}</span>
            <span style={{ fontSize: '0.68rem', color: '#34D399', background: 'rgba(16, 185, 129, 0.15)', padding: '2px 6px', borderRadius: '4px' }}>
              {t.status}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}

export function CreateEventEntryCard({ category, event_type, title, city, date_str, onStartSetup }) {
  return (
    <div style={{
      background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.95), rgba(15, 23, 42, 0.98))',
      border: '1px solid rgba(139, 92, 246, 0.4)',
      borderRadius: '16px',
      padding: '20px',
      marginTop: '10px',
      boxShadow: '0 8px 24px rgba(139, 92, 246, 0.15)',
      maxWidth: '480px'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
        <div style={{ background: 'linear-gradient(135deg, #8B5CF6, #EC4899)', padding: '10px', borderRadius: '12px' }}>
          <Sparkles size={20} color="white" />
        </div>
        <div>
          <h4 style={{ fontSize: '1.2rem', fontWeight: 800, color: 'white', margin: 0 }}>Create Your Event</h4>
          <p style={{ fontSize: '0.88rem', color: '#A78BFA', margin: '4px 0 0 0', fontWeight: 700 }}>
            Organizer Setup
          </p>
        </div>
      </div>

      <p style={{ fontSize: '0.9rem', color: '#94A3B8', marginBottom: '18px', lineHeight: 1.5 }}>
        Sure — create your event using the event setup form.
      </p>

      <button
        onClick={() => onStartSetup && onStartSetup({ category: category || 'Technology', event_type: event_type || 'Workshop', title, city, date_str })}
        style={{
          width: '100%',
          background: 'linear-gradient(135deg, #10B981, #059669)',
          border: 'none',
          color: 'white',
          padding: '12px',
          borderRadius: '12px',
          fontSize: '0.95rem',
          fontWeight: 700,
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '8px',
          boxShadow: '0 4px 16px rgba(16, 185, 129, 0.3)',
          minHeight: '44px'
        }}
      >
        <Sparkles size={16} /> Create Event
      </button>
    </div>
  );
}

export function WelcomeScreenCard({ onQuickAction }) {

  const actions = [
    { title: 'Book Tickets', desc: 'Search & buy event passes', icon: '🎫', prompt: 'Show upcoming events in Bangalore' },
    { title: 'Find Events', desc: 'Explore tech, music & workshops', icon: '🔎', prompt: 'Show me music concerts this weekend' },
    { title: 'My Tickets', desc: 'View QR passes & PDF invoices', icon: '🎟️', prompt: 'Show my booked tickets' },
    { title: 'Create Event', desc: 'AI-assisted event publishing', icon: '🎤', prompt: 'I want to create a tech workshop event' }
  ];

  return (
    <div style={{
      textAlign: 'center',
      padding: '36px 28px',
      maxWidth: '640px',
      margin: '24px auto',
      background: 'rgba(15, 23, 42, 0.5)',
      border: '1px solid rgba(139, 92, 246, 0.25)',
      borderRadius: '24px',
      backdropFilter: 'blur(12px)'
    }}>
      <div style={{ fontSize: '3rem', marginBottom: '14px' }}>🤖</div>
      <h2 style={{ fontSize: '1.6rem', fontWeight: 800, color: '#F8FAFC', margin: '0 0 10px 0' }}>
        Welcome to ChatAssist
      </h2>
      <p style={{ fontSize: '0.95rem', color: '#94A3B8', margin: '0 0 28px 0', lineHeight: 1.6 }}>
        Your AI conversational assistant for event discovery, ticket bookings, instant QR passes, and organizer management.
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
        {actions.map((act, idx) => (
          <button
            key={idx}
            onClick={() => onQuickAction(act.prompt)}
            style={{
              background: 'rgba(30, 41, 59, 0.7)',
              border: '1px solid rgba(139, 92, 246, 0.25)',
              borderRadius: '16px',
              padding: '16px',
              textAlign: 'left',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
              display: 'flex',
              flexDirection: 'column',
              gap: '6px',
              minHeight: '80px'
            }}
            onMouseOver={(e) => e.currentTarget.style.borderColor = '#8B5CF6'}
            onMouseOut={(e) => e.currentTarget.style.borderColor = 'rgba(139, 92, 246, 0.25)'}
          >
            <span style={{ fontSize: '1.6rem' }}>{act.icon}</span>
            <span style={{ color: '#F1F5F9', fontWeight: 700, fontSize: '0.95rem' }}>{act.title}</span>
            <span style={{ color: '#64748B', fontSize: '0.8rem' }}>{act.desc}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

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
    <div style={{
      background: 'rgba(30, 41, 59, 0.9)',
      border: '1px solid rgba(239, 68, 68, 0.4)',
      borderRadius: '14px',
      padding: '18px',
      marginTop: '10px',
      color: 'white'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px', color: '#F87171', fontWeight: 700, fontSize: '0.95rem' }}>
        <AlertCircle size={18} /> Cancellation & Refund Request
      </div>
      <p style={{ fontSize: '0.88rem', color: '#E2E8F0', margin: '0 0 12px 0' }}>
        Ticket <strong>{ticket_number}</strong> for <em>{event_title || 'Event'}</em> ({formatINR(price_paid)}) is eligible for a 100% full refund under standard cancellation policy.
      </p>

      {!done ? (
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            onClick={handleCancel}
            disabled={cancelling}
            style={{
              background: '#EF4444',
              border: 'none',
              color: 'white',
              padding: '10px 16px',
              borderRadius: '10px',
              fontWeight: 700,
              fontSize: '0.88rem',
              minHeight: '40px',
              cursor: cancelling ? 'wait' : 'pointer'
            }}
          >
            {cancelling ? 'Processing Refund...' : 'Confirm Cancellation'}
          </button>
        </div>
      ) : (
        <div style={{ color: '#10B981', fontWeight: 700, fontSize: '0.88rem' }}>
          ✅ Cancellation processed successfully! Refund credited.
        </div>
      )}
    </div>
  );
}


