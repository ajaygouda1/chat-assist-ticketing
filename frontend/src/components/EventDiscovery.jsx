import React, { useState } from 'react';
import { Calendar, MapPin, Ticket, Tag, Users, Sparkles } from 'lucide-react';

export default function EventDiscovery({ events, onBookEvent, selectedCategory, setSelectedCategory }) {
  const categories = ['All', 'Tech', 'Workshop', 'Music', 'Entertainment'];

  const filteredEvents = selectedCategory === 'All' 
    ? events 
    : events.filter(e => e.category.toLowerCase() === selectedCategory.toLowerCase());

  return (
    <div style={{ padding: '0 24px 40px 24px' }}>
      {/* Category Pills Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'white' }}>Upcoming Events</h2>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>Explore verified tickets with real-time atomic capacity management</p>
        </div>

        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          {categories.map(cat => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              style={{
                background: selectedCategory === cat ? 'linear-gradient(135deg, #3B82F6, #8B5CF6)' : 'rgba(255, 255, 255, 0.05)',
                color: selectedCategory === cat ? 'white' : 'var(--text-muted)',
                border: '1px solid var(--border-glass)',
                padding: '8px 16px',
                borderRadius: '20px',
                fontSize: '0.85rem',
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all 0.2s ease'
              }}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Events Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '24px' }}>
        {filteredEvents.map(ev => (
          <div key={ev.id} className="glass-panel" style={{ overflow: 'hidden', display: 'flex', flexDirection: 'column', transition: 'all 0.3s ease' }}>
            {/* Event Image Banner */}
            <div style={{ position: 'relative', height: '180px', overflow: 'hidden' }}>
              <img 
                src={ev.image_url} 
                alt={ev.title} 
                style={{ width: '100%', height: '100%', objectFit: 'cover' }} 
              />
              <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(to top, rgba(11, 15, 25, 0.95), transparent)' }} />
              
              <div style={{ position: 'absolute', top: '12px', left: '12px', display: 'flex', gap: '6px' }}>
                <span className="badge" style={{ background: 'rgba(15, 23, 42, 0.85)', color: '#60A5FA', border: '1px solid rgba(59, 130, 246, 0.4)' }}>
                  {ev.category}
                </span>
              </div>

              <div style={{ position: 'absolute', top: '12px', right: '12px' }}>
                <span className="badge" style={{ background: ev.available_tickets < 10 ? 'rgba(239, 68, 68, 0.85)' : 'rgba(16, 185, 129, 0.85)', color: 'white' }}>
                  {ev.available_tickets} seats left
                </span>
              </div>
            </div>

            {/* Event Info */}
            <div style={{ padding: '20px', flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'white', marginBottom: '8px' }}>{ev.title}</h3>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '16px', lineHeight: '1.5' }}>
                  {ev.description}
                </p>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '16px', fontSize: '0.8rem', color: '#CBD5E1' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Calendar size={14} color="#60A5FA" /> <span>{ev.date_str}</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <MapPin size={14} color="#F472B6" /> <span>{ev.location}</span>
                  </div>
                </div>
              </div>

              {/* Price & CTA */}
              <div style={{ borderTop: '1px solid var(--border-glass)', paddingTop: '16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block' }}>Ticket Price</span>
                  <span style={{ fontSize: '1.25rem', fontWeight: 800, color: '#34D399' }}>₹{ev.price}</span>
                </div>

                <button
                  onClick={() => onBookEvent(ev)}
                  className="gradient-btn"
                  style={{ padding: '10px 18px', fontSize: '0.875rem' }}
                >
                  <Ticket size={16} /> Book Ticket
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
