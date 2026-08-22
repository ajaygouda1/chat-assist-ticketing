import React, { useState, useEffect } from 'react';
import axios from 'axios';

export default function EventComparisonModal({ eventIds, onClose }) {
  const [comparisonData, setComparisonData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (eventIds && eventIds.length >= 2) {
      fetchComparison();
    }
  }, [eventIds]);

  const fetchComparison = async () => {
    setLoading(true);
    try {
      const res = await axios.post('/api/v1/events/compare', { event_ids: eventIds });
      setComparisonData(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (!eventIds || eventIds.length < 2) return null;

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      background: 'rgba(0,0,0,0.75)',
      backdropFilter: 'blur(4px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 9999,
      padding: '16px'
    }}>
      <div style={{
        background: '#0f172a',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        borderRadius: '16px',
        padding: '24px',
        color: '#fff',
        maxWidth: '850px',
        width: '100%',
        maxHeight: '90vh',
        overflowY: 'auto'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <div>
            <h3 style={{ margin: 0, fontSize: '20px', fontWeight: 600 }}>📊 Event Comparison Matrix</h3>
            <p style={{ margin: '4px 0 0', fontSize: '13px', color: '#94a3b8' }}>Side-by-side event comparison with grounded AI recommendations</p>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: '#94a3b8', fontSize: '20px', cursor: 'pointer' }}>✕</button>
        </div>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '40px 0', color: '#94a3b8' }}>Analyzing events...</div>
        ) : comparisonData ? (
          <>
            {/* AI Grounded Summary Banner */}
            <div style={{
              background: 'rgba(99, 102, 241, 0.12)',
              border: '1px solid rgba(99, 102, 241, 0.3)',
              borderRadius: '10px',
              padding: '12px 16px',
              marginBottom: '20px',
              fontSize: '13px',
              color: '#a5b4fc',
              display: 'flex',
              alignItems: 'center',
              gap: '10px'
            }}>
              <span style={{ fontSize: '16px' }}>🤖</span>
              <span>{comparisonData.ai_recommendation_note}</span>
            </div>

            {/* Comparison Table */}
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
                  <th style={{ textAlign: 'left', padding: '12px', color: '#94a3b8' }}>Feature</th>
                  {comparisonData.events.map((ev) => (
                    <th key={ev.id} style={{ textAlign: 'left', padding: '12px', color: '#38bdf8', fontWeight: 600 }}>{ev.title}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                  <td style={{ padding: '12px', fontWeight: 500, color: '#e2e8f0' }}>Price</td>
                  {comparisonData.events.map((ev) => (
                    <td key={ev.id} style={{ padding: '12px', color: '#22c55e', fontWeight: 600 }}>₹{ev.price}</td>
                  ))}
                </tr>
                <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                  <td style={{ padding: '12px', fontWeight: 500, color: '#e2e8f0' }}>Category</td>
                  {comparisonData.events.map((ev) => (
                    <td key={ev.id} style={{ padding: '12px', color: '#cbd5e1' }}>{ev.category}</td>
                  ))}
                </tr>
                <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                  <td style={{ padding: '12px', fontWeight: 500, color: '#e2e8f0' }}>Location</td>
                  {comparisonData.events.map((ev) => (
                    <td key={ev.id} style={{ padding: '12px', color: '#cbd5e1' }}>{ev.location}</td>
                  ))}
                </tr>
                <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                  <td style={{ padding: '12px', fontWeight: 500, color: '#e2e8f0' }}>Date</td>
                  {comparisonData.events.map((ev) => (
                    <td key={ev.id} style={{ padding: '12px', color: '#cbd5e1' }}>{ev.date}</td>
                  ))}
                </tr>
                <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                  <td style={{ padding: '12px', fontWeight: 500, color: '#e2e8f0' }}>Tickets Left</td>
                  {comparisonData.events.map((ev) => (
                    <td key={ev.id} style={{ padding: '12px', color: '#cbd5e1' }}>{ev.available_tickets} / {ev.total_capacity}</td>
                  ))}
                </tr>
                <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                  <td style={{ padding: '12px', fontWeight: 500, color: '#e2e8f0' }}>Refund Policy</td>
                  {comparisonData.events.map((ev) => (
                    <td key={ev.id} style={{ padding: '12px', color: '#f59e0b', fontWeight: 500 }}>{ev.refund_policy}</td>
                  ))}
                </tr>
                <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                  <td style={{ padding: '12px', fontWeight: 500, color: '#e2e8f0' }}>Certificate</td>
                  {comparisonData.events.map((ev) => (
                    <td key={ev.id} style={{ padding: '12px', color: '#cbd5e1' }}>{ev.certificate_provided}</td>
                  ))}
                </tr>
              </tbody>
            </table>
          </>
        ) : null}
      </div>
    </div>
  );
}
