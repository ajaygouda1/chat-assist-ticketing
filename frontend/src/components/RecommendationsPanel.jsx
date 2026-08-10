import React from 'react';
import { Sparkles, Calendar, MapPin, Ticket } from 'lucide-react';

export default function RecommendationsPanel({ recommendations, onBookEvent }) {
  if (!recommendations || recommendations.length === 0) return null;

  return (
    <div style={{ margin: '0 24px 32px 24px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
        <Sparkles color="#A78BFA" size={20} />
        <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'white' }}>Recommended For You</h2>
        <span className="badge badge-intent" style={{ marginLeft: '8px' }}>Content Embedding Recommender</span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '16px' }}>
        {recommendations.map((ev) => (
          <div key={ev.id} className="glass-panel" style={{ padding: '16px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', transition: 'all 0.2s ease', cursor: 'pointer' }}>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                <span className="badge" style={{ background: 'rgba(59, 130, 246, 0.15)', color: '#60A5FA', border: '1px solid rgba(59, 130, 246, 0.3)' }}>
                  {ev.category}
                </span>
                <span style={{ fontSize: '0.875rem', fontWeight: 700, color: '#34D399' }}>₹{ev.price}</span>
              </div>
              <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'white', marginBottom: '8px' }}>{ev.title}</h3>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '12px', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                {ev.description}
              </p>
            </div>

            <div style={{ borderTop: '1px solid var(--border-glass)', paddingTop: '12px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <MapPin size={12} /> {ev.location.split(',')[0]}
              </span>
              <button 
                onClick={() => onBookEvent(ev)}
                className="gradient-btn"
                style={{ padding: '6px 12px', fontSize: '0.75rem', borderRadius: '6px' }}
              >
                <Ticket size={12} /> Book
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
