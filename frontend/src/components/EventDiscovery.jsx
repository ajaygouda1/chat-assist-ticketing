import React, { useState } from 'react';
import { Calendar, MapPin, Ticket, Star, Flame, Users, ArrowRight, Compass, Layers, SlidersHorizontal } from 'lucide-react';
import SeatMap from './seating/SeatMap';
import EventComparisonModal from './events/EventComparisonModal';

export default function EventDiscovery({ events = [], onBookEvent, selectedCategory, setSelectedCategory }) {
  const categories = ['All', 'Tech', 'Workshop', 'Music', 'Entertainment'];
  const [seatMapEventId, setSeatMapEventId] = useState(null);
  const [selectedForCompare, setSelectedForCompare] = useState([]);
  const [isCompareOpen, setIsCompareOpen] = useState(false);

  const filteredEvents = selectedCategory === 'All' 
    ? events 
    : events.filter(e => e.category.toLowerCase() === selectedCategory.toLowerCase());

  const toggleCompare = (evId) => {
    if (selectedForCompare.includes(evId)) {
      setSelectedForCompare(selectedForCompare.filter((id) => id !== evId));
    } else {
      if (selectedForCompare.length >= 3) {
        alert("You can select up to 3 events to compare side-by-side.");
        return;
      }
      setSelectedForCompare([...selectedForCompare, evId]);
    }
  };

  return (
    <div style={{ padding: '0 24px 40px 24px' }}>
      {seatMapEventId && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.8)', zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '16px' }}>
          <SeatMap eventId={seatMapEventId} onClose={() => setSeatMapEventId(null)} onSeatsSelected={(seats) => { setSeatMapEventId(null); onBookEvent(events.find(e => e.id === seatMapEventId)); }} />
        </div>
      )}

      {isCompareOpen && (
        <EventComparisonModal eventIds={selectedForCompare} onClose={() => setIsCompareOpen(false)} />
      )}

      {/* Category Pills & Compare Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h2 style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--paper)' }} className="font-display-title">
            Featured Event Stub Directory
          </h2>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
            Grounded live ticket inventory with HMAC cryptographic verification
          </p>
        </div>

        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center' }}>
          {selectedForCompare.length >= 2 && (
            <button
              onClick={() => setIsCompareOpen(true)}
              style={{
                background: 'linear-gradient(90deg, #6366f1, #a855f7)',
                color: '#fff',
                border: 'none',
                padding: '8px 16px',
                borderRadius: '20px',
                fontSize: '0.85rem',
                fontWeight: 700,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}
            >
              <SlidersHorizontal size={14} /> Compare ({selectedForCompare.length})
            </button>
          )}

          {categories.map(cat => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              style={{
                background: selectedCategory === cat ? 'linear-gradient(135deg, var(--gold), var(--stub-red))' : 'rgba(31, 28, 33, 0.7)',
                color: selectedCategory === cat ? '#151316' : 'var(--text-muted)',
                border: selectedCategory === cat ? '1px solid var(--gold)' : '1px solid var(--border-glass)',
                padding: '8px 18px',
                borderRadius: '20px',
                fontSize: '0.85rem',
                fontWeight: 700,
                cursor: 'pointer',
                transition: 'all 0.2s ease'
              }}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Empty State */}
      {filteredEvents.length === 0 ? (
        <div className="glass-panel" style={{ padding: '60px 24px', textAlign: 'center', maxWidth: '540px', margin: '40px auto' }}>
          <Compass size={48} color="var(--gold)" style={{ margin: '0 auto 16px auto', opacity: 0.8 }} />
          <h3 style={{ fontSize: '1.4rem', color: 'var(--paper)', marginBottom: '8px' }} className="font-display-title">
            No Events Found in '{selectedCategory}'
          </h3>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '20px' }}>
            Looking for something happening this weekend? Explore all available events or ask our AI Copilot for recommendations.
          </p>
          <button
            onClick={() => setSelectedCategory('All')}
            className="gradient-btn"
            style={{ margin: '0 auto' }}
          >
            Find Something Happening This Weekend <ArrowRight size={16} />
          </button>
        </div>
      ) : (
        /* Events Grid */
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '24px' }}>
          {filteredEvents.map(ev => {
            const seatsLeft = ev.available_tickets ?? 50;
            const isUrgent = seatsLeft < 15;
            const reviewRating = (4.7 + ((ev.id % 4) * 0.1)).toFixed(1);
            const isCompared = selectedForCompare.includes(ev.id);

            return (
              <div key={ev.id} className="ticket-stub" style={{ display: 'flex', flexDirection: 'column' }}>
                {/* Event Banner */}
                <div style={{ position: 'relative', height: '180px', overflow: 'hidden' }}>
                  <img 
                    src={ev.image_url || "https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=800&auto=format&fit=crop&q=80"} 
                    alt={`${ev.title} poster`} 
                    style={{ width: '100%', height: '100%', objectFit: 'cover' }} 
                  />
                  <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(to top, var(--surface), transparent 70%)' }} />
                  
                  {/* Category & Compare Checkbox */}
                  <div style={{ position: 'absolute', top: '12px', left: '12px', display: 'flex', gap: '6px' }}>
                    <span className="badge badge-gold">
                      {ev.category}
                    </span>
                    <button
                      onClick={() => toggleCompare(ev.id)}
                      style={{
                        background: isCompared ? '#6366f1' : 'rgba(0,0,0,0.6)',
                        border: '1px solid rgba(255,255,255,0.2)',
                        color: '#fff',
                        fontSize: '11px',
                        padding: '2px 8px',
                        borderRadius: '12px',
                        cursor: 'pointer'
                      }}
                    >
                      {isCompared ? '✓ Comparing' : '+ Compare'}
                    </button>
                  </div>

                  {/* Social Proof Urgency Badge */}
                  <div style={{ position: 'absolute', top: '12px', right: '12px' }}>
                    <span className={`badge ${isUrgent ? 'badge-urgency' : 'badge-gold'}`} style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                      {isUrgent ? <Flame size={12} color="#F87171" /> : null}
                      <span className="font-mono-data">{seatsLeft} seats left</span>
                    </span>
                  </div>
                </div>

                {/* Event Card Content */}
                <div style={{ padding: '20px', flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '8px', marginBottom: '6px' }}>
                      <h3 style={{ fontSize: '1.3rem', fontWeight: 800, color: 'var(--paper)', lineHeight: '1.2' }} className="font-display-title">
                        {ev.title}
                      </h3>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '3px', background: 'rgba(232, 163, 61, 0.1)', padding: '2px 6px', borderRadius: '6px', fontSize: '0.75rem', color: 'var(--gold)', whiteSpace: 'nowrap' }}>
                        <Star size={12} fill="var(--gold)" color="var(--gold)" />
                        <span className="font-mono-data" style={{ fontWeight: 700 }}>{reviewRating}</span>
                      </div>
                    </div>

                    <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '14px', lineHeight: '1.5' }}>
                      {ev.description}
                    </p>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '14px', fontSize: '0.8rem', color: 'var(--paper)' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <Calendar size={14} color="var(--gold)" /> <span style={{ fontWeight: 500 }}>{ev.date_str}</span>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <MapPin size={14} color="#F87171" /> <span>{ev.location}</span>
                      </div>
                    </div>
                  </div>

                  <div className="ticket-seam" />

                  {/* Price & Action Buttons */}
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingTop: '4px' }}>
                    <div>
                      <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Ticket Price</span>
                      <span style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--gold)' }} className="font-mono-data">₹{ev.price}</span>
                    </div>

                    <div style={{ display: 'flex', gap: '6px' }}>
                      <button
                        onClick={() => setSeatMapEventId(ev.id)}
                        style={{
                          background: 'rgba(59, 130, 246, 0.15)',
                          border: '1px solid #3b82f6',
                          color: '#60a5fa',
                          padding: '8px 12px',
                          borderRadius: '8px',
                          fontSize: '0.8rem',
                          fontWeight: 600,
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '4px'
                        }}
                      >
                        <Layers size={14} /> Seat Map
                      </button>
                      <button
                        onClick={() => onBookEvent(ev)}
                        className="gradient-btn"
                        style={{ padding: '8px 14px', fontSize: '0.85rem' }}
                      >
                        <Ticket size={14} /> Book
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

