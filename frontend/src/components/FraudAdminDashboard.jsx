import React, { useEffect, useState } from 'react';
import { ShieldAlert, AlertTriangle, CheckCircle, RefreshCw } from 'lucide-react';
import axios from 'axios';

export default function FraudAdminDashboard() {
  const [flags, setFlags] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchFraudFlags();
  }, []);

  const fetchFraudFlags = async () => {
    setLoading(true);
    try {
      const res = await axios.get('/api/v1/admin/fraud-flags');
      setFlags(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleReviewAction = async (flagId, action) => {
    try {
      await axios.post(`/api/v1/admin/fraud-flags/${flagId}/review?action=${action}`);
      fetchFraudFlags();
    } catch (err) {
      alert('Review action failed');
    }
  };

  return (
    <div style={{ padding: '0 24px 40px 24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <ShieldAlert color="#F87171" size={24} />
            <h2 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'white' }}>Fraud & Anomaly Detection Dashboard</h2>
          </div>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>Powered by scikit-learn IsolationForest (monitoring booking velocity, failed payments, multi-IPs)</p>
        </div>

        <button 
          onClick={fetchFraudFlags} 
          style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border-glass)', color: 'white', padding: '8px 14px', borderRadius: '10px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem' }}
        >
          <RefreshCw size={14} /> Refresh Logs
        </button>
      </div>

      <div className="glass-panel" style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.875rem' }}>
          <thead>
            <tr style={{ background: 'rgba(15, 23, 42, 0.8)', borderBottom: '1px solid var(--border-glass)' }}>
              <th style={{ padding: '14px 16px', color: 'var(--text-muted)' }}>ID</th>
              <th style={{ padding: '14px 16px', color: 'var(--text-muted)' }}>User ID</th>
              <th style={{ padding: '14px 16px', color: 'var(--text-muted)' }}>Anomaly Score</th>
              <th style={{ padding: '14px 16px', color: 'var(--text-muted)' }}>Trigger Reason</th>
              <th style={{ padding: '14px 16px', color: 'var(--text-muted)' }}>Status</th>
              <th style={{ padding: '14px 16px', color: 'var(--text-muted)' }}>Manual Review Action</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={6} style={{ padding: '20px', textAlign: 'center', color: 'var(--text-muted)' }}>Running anomaly check...</td></tr>
            ) : flags.map(f => (
              <tr key={f.id} style={{ borderBottom: '1px solid var(--border-glass)' }}>
                <td style={{ padding: '14px 16px', fontWeight: 700, color: 'white' }}>#{f.id}</td>
                <td style={{ padding: '14px 16px', color: '#60A5FA' }}>User-{f.user_id}</td>
                <td style={{ padding: '14px 16px' }}>
                  <span className="badge badge-anomaly">
                    <AlertTriangle size={12} /> Score: {f.score.toFixed(2)}
                  </span>
                </td>
                <td style={{ padding: '14px 16px', color: 'white', maxWidth: '300px' }}>{f.reason}</td>
                <td style={{ padding: '14px 16px' }}>
                  <span className="badge" style={{
                    background: f.status === 'CLEARED' ? 'rgba(16, 185, 129, 0.2)' : f.status === 'CONFIRMED' ? 'rgba(239, 68, 68, 0.2)' : 'rgba(245, 158, 11, 0.2)',
                    color: f.status === 'CLEARED' ? '#34D399' : f.status === 'CONFIRMED' ? '#F87171' : '#FBBF24'
                  }}>
                    {f.status}
                  </span>
                </td>
                <td style={{ padding: '14px 16px' }}>
                  {f.status === 'PENDING_REVIEW' ? (
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <button 
                        onClick={() => handleReviewAction(f.id, 'CLEARED')}
                        style={{ background: 'rgba(16, 185, 129, 0.2)', border: '1px solid rgba(16, 185, 129, 0.4)', color: '#34D399', padding: '4px 10px', borderRadius: '6px', cursor: 'pointer', fontSize: '0.75rem', fontWeight: 600 }}
                      >
                        Clear (Safe)
                      </button>
                      <button 
                        onClick={() => handleReviewAction(f.id, 'CONFIRMED')}
                        style={{ background: 'rgba(239, 68, 68, 0.2)', border: '1px solid rgba(239, 68, 68, 0.4)', color: '#F87171', padding: '4px 10px', borderRadius: '6px', cursor: 'pointer', fontSize: '0.75rem', fontWeight: 600 }}
                      >
                        Confirm Fraud
                      </button>
                    </div>
                  ) : (
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Reviewed</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
