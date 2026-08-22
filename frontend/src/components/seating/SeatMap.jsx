import React, { useState, useEffect } from 'react';
import axios from 'axios';

export default function SeatMap({ eventId, onSeatsSelected, onClose }) {
  const [seatData, setSeatData] = useState({});
  const [selectedSeats, setSelectedSeats] = useState([]);
  const [loading, setLoading] = useState(true);
  const [holding, setHolding] = useState(false);
  const [holdTimer, setHoldTimer] = useState(600); // 10 mins
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    fetchSeatMap();
  }, [eventId]);

  useEffect(() => {
    let interval = null;
    if (selectedSeats.length > 0 && holdTimer > 0) {
      interval = setInterval(() => {
        setHoldTimer((prev) => prev - 1);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [selectedSeats, holdTimer]);

  const fetchSeatMap = async () => {
    setLoading(true);
    setErrorMsg('');
    try {
      const res = await axios.get(`/api/v1/events/${eventId}/seatmap`);
      setSeatData(res.data);
    } catch (err) {
      console.error(err);
      setErrorMsg('Failed to load venue seat map');
    } finally {
      setLoading(false);
    }
  };

  const handleSeatClick = (seat) => {
    if (seat.status === 'SOLD' || seat.status === 'BLOCKED') return;
    if (seat.status === 'HELD' && !selectedSeats.includes(seat.seat_code)) return;

    if (selectedSeats.includes(seat.seat_code)) {
      setSelectedSeats(selectedSeats.filter((c) => c !== seat.seat_code));
    } else {
      if (selectedSeats.length >= 6) {
        setErrorMsg('You can select a maximum of 6 reserved seats per booking.');
        return;
      }
      setErrorMsg('');
      setSelectedSeats([...selectedSeats, seat.seat_code]);
    }
  };

  const handleConfirmHold = async () => {
    if (selectedSeats.length === 0) return;
    setHolding(true);
    setErrorMsg('');
    try {
      await axios.post(`/api/v1/events/${eventId}/hold-seats`, {
        seat_codes: selectedSeats,
      });
      if (onSeatsSelected) {
        onSeatsSelected(selectedSeats);
      }
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || 'Seat hold failed');
    } finally {
      setHolding(false);
    }
  };

  const formatTimer = (seconds) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s < 10 ? '0' : ''}${s}`;
  };

  return (
    <div style={{
      background: 'rgba(15, 23, 42, 0.95)',
      borderRadius: '16px',
      border: '1px solid rgba(255, 255, 255, 0.1)',
      padding: '24px',
      color: '#fff',
      maxWidth: '720px',
      margin: '0 auto'
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div>
          <h3 style={{ margin: 0, fontSize: '18px', fontWeight: 600 }}>Interactive Venue Seat Map</h3>
          <p style={{ margin: '4px 0 0', fontSize: '13px', color: '#94a3b8' }}>Select your seats (10-minute temporary reservation lock)</p>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            style={{ background: 'none', border: 'none', color: '#94a3b8', fontSize: '20px', cursor: 'pointer' }}
          >
            ✕
          </button>
        )}
      </div>

      {errorMsg && (
        <div style={{ background: 'rgba(239, 68, 68, 0.15)', border: '1px solid #ef4444', color: '#f87171', padding: '10px 14px', borderRadius: '8px', fontSize: '13px', marginBottom: '16px' }}>
          {errorMsg}
        </div>
      )}

      {/* Stage Banner */}
      <div style={{
        background: 'linear-gradient(90deg, #6366f1, #a855f7)',
        borderRadius: '8px',
        padding: '8px',
        textAlign: 'center',
        fontWeight: 700,
        letterSpacing: '2px',
        fontSize: '12px',
        marginBottom: '24px',
        textTransform: 'uppercase',
        boxShadow: '0 4px 12px rgba(99, 102, 241, 0.3)'
      }}>
        ────────────────── STAGE ──────────────────
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px 0', color: '#94a3b8' }}>Loading seat layout...</div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {Object.entries(seatData).map(([secName, seats]) => (
            <div key={secName} style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '16px', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.05)' }}>
              <div style={{ fontSize: '14px', fontWeight: 600, color: '#e2e8f0', marginBottom: '12px', display: 'flex', justifyContent: 'space-between' }}>
                <span>Section: {secName}</span>
                <span style={{ fontSize: '12px', color: '#38bdf8' }}>₹{seats[0]?.price || 0}</span>
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', justifyContent: 'center' }}>
                {seats.map((seat) => {
                  const isSelected = selectedSeats.includes(seat.seat_code);
                  let bg = '#1e293b';
                  let border = '1px solid #475569';
                  let color = '#cbd5e1';

                  if (seat.status === 'SOLD') {
                    bg = '#dc2626';
                    border = '1px solid #b91c1c';
                    color = '#fff';
                  } else if (seat.status === 'HELD' && !isSelected) {
                    bg = '#d97706';
                    border = '1px solid #b45309';
                    color = '#fff';
                  } else if (isSelected) {
                    bg = '#22c55e';
                    border = '1px solid #16a34a';
                    color = '#fff';
                  }

                  return (
                    <button
                      key={seat.id}
                      onClick={() => handleSeatClick(seat)}
                      disabled={seat.status === 'SOLD' || (seat.status === 'HELD' && !isSelected)}
                      title={`${seat.seat_code} - ₹${seat.price} (${seat.status})`}
                      style={{
                        width: '38px',
                        height: '38px',
                        borderRadius: '8px',
                        background: bg,
                        border: border,
                        color: color,
                        fontSize: '11px',
                        fontWeight: 600,
                        cursor: seat.status === 'SOLD' ? 'not-allowed' : 'pointer',
                        transition: 'transform 0.1s ease',
                        boxShadow: isSelected ? '0 0 8px #22c55e' : 'none'
                      }}
                    >
                      {seat.seat_code}
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Legend */}
      <div style={{ display: 'flex', gap: '16px', justifyContent: 'center', marginTop: '20px', fontSize: '12px', color: '#94a3b8' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ width: '12px', height: '12px', borderRadius: '3px', background: '#1e293b', border: '1px solid #475569' }}></span> Available
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ width: '12px', height: '12px', borderRadius: '3px', background: '#22c55e' }}></span> Selected
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ width: '12px', height: '12px', borderRadius: '3px', background: '#d97706' }}></span> Held
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ width: '12px', height: '12px', borderRadius: '3px', background: '#dc2626' }}></span> Sold
        </div>
      </div>

      {/* Action Footer */}
      <div style={{ marginTop: '24px', paddingTop: '16px', borderTop: '1px solid rgba(255,255,255,0.1)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <span style={{ fontSize: '13px', color: '#94a3b8' }}>Selected: </span>
          <span style={{ fontSize: '14px', fontWeight: 600, color: '#38bdf8' }}>
            {selectedSeats.length > 0 ? selectedSeats.join(', ') : 'None'}
          </span>
        </div>
        <button
          onClick={handleConfirmHold}
          disabled={selectedSeats.length === 0 || holding}
          style={{
            background: selectedSeats.length > 0 ? 'linear-gradient(90deg, #6366f1, #a855f7)' : '#334155',
            color: '#fff',
            border: 'none',
            padding: '10px 20px',
            borderRadius: '8px',
            fontWeight: 600,
            cursor: selectedSeats.length > 0 ? 'pointer' : 'not-allowed',
            transition: 'opacity 0.2s'
          }}
        >
          {holding ? 'Locking Seats...' : 'Confirm Seat Selection'}
        </button>
      </div>
    </div>
  );
}
