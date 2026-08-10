import React, { useState } from 'react';
import { ShieldCheck, Users, DollarSign, Calendar, Lock, AlertCircle, FileText, CheckCircle } from 'lucide-react';

export default function SuperAdminDashboard() {
  const [users] = useState([
    { id: 1, name: 'Ajay Kumar', email: 'demo@chatassist.com', role: 'customer', status: 'ACTIVE' },
    { id: 2, name: 'Tech Events India', email: 'organizer@techconf.com', role: 'organizer', status: 'VERIFIED' },
    { id: 3, name: 'CyberSec Corp', email: 'admin@cybersec.org', role: 'organizer', status: 'VERIFIED' },
    { id: 4, name: 'Suspicious Bot Account', email: 'bot99@tempmail.com', role: 'customer', status: 'SUSPENDED' },
  ]);

  const [systemLogs] = useState([
    { timestamp: '11:50:04', event: 'JWT Auth token generated for user id 1', level: 'INFO' },
    { timestamp: '11:49:12', event: 'IsolationForest flagged transaction #102 anomaly score 0.88', level: 'WARN' },
    { timestamp: '11:48:30', event: 'GST Tax invoice INV-2026-F982A1 rendered (PDF 18% tax)', level: 'INFO' },
    { timestamp: '11:45:00', event: 'Atomic reservation decrement lock executed on Event ID 1', level: 'INFO' },
  ]);

  return (
    <div style={{ padding: '0 24px 40px 24px' }}>
      <div style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Lock color="#60A5FA" size={24} />
          <h2 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'white' }}>Super Admin Platform Control Panel</h2>
        </div>
        <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>Monitor platform revenue, user roles, organizer verification, and security audit logs</p>
      </div>

      {/* Metrics Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px', marginBottom: '32px' }}>
        <div className="glass-panel" style={{ padding: '20px' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Total Platform Users</span>
          <h3 style={{ fontSize: '1.75rem', fontWeight: 800, color: 'white' }}>1,482</h3>
          <span className="badge badge-grounded" style={{ marginTop: '8px' }}>+12% this month</span>
        </div>

        <div className="glass-panel" style={{ padding: '20px' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Verified Organizers</span>
          <h3 style={{ fontSize: '1.75rem', fontWeight: 800, color: '#60A5FA' }}>84</h3>
          <span className="badge badge-intent" style={{ marginTop: '8px' }}>100% Verified</span>
        </div>

        <div className="glass-panel" style={{ padding: '20px' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Gross Revenue</span>
          <h3 style={{ fontSize: '1.75rem', fontWeight: 800, color: '#34D399' }}>₹2,84,500</h3>
          <span className="badge badge-grounded" style={{ marginTop: '8px' }}>₹51,210 GST Collected</span>
        </div>

        <div className="glass-panel" style={{ padding: '20px' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Active Events</span>
          <h3 style={{ fontSize: '1.75rem', fontWeight: 800, color: '#C084FC' }}>28</h3>
          <span className="badge badge-intent" style={{ marginTop: '8px' }}>0 Oversold Seats</span>
        </div>
      </div>

      {/* User Management Table */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '24px' }}>
        <div className="glass-panel" style={{ padding: '20px' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'white', marginBottom: '16px' }}>User & Organizer Accounts</h3>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-glass)', color: 'var(--text-muted)' }}>
                  <th style={{ padding: '10px' }}>User</th>
                  <th style={{ padding: '10px' }}>Role</th>
                  <th style={{ padding: '10px' }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {users.map(u => (
                  <tr key={u.id} style={{ borderBottom: '1px solid var(--border-glass)' }}>
                    <td style={{ padding: '10px' }}>
                      <div style={{ fontWeight: 600, color: 'white' }}>{u.name}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{u.email}</div>
                    </td>
                    <td style={{ padding: '10px', textTransform: 'capitalize' }}>{u.role}</td>
                    <td style={{ padding: '10px' }}>
                      <span className="badge" style={{
                        background: u.status === 'SUSPENDED' ? 'rgba(239, 68, 68, 0.2)' : 'rgba(16, 185, 129, 0.2)',
                        color: u.status === 'SUSPENDED' ? '#F87171' : '#34D399'
                      }}>
                        {u.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* System Logs Feed */}
        <div className="glass-panel" style={{ padding: '20px' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'white', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <FileText size={18} color="#C084FC" /> System Security & Audit Log
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontFamily: 'monospace', fontSize: '0.8rem' }}>
            {systemLogs.map((log, idx) => (
              <div key={idx} style={{ background: 'rgba(15, 23, 42, 0.8)', border: '1px solid var(--border-glass)', padding: '10px 12px', borderRadius: '8px', display: 'flex', gap: '10px' }}>
                <span style={{ color: '#60A5FA' }}>[{log.timestamp}]</span>
                <span style={{ color: log.level === 'WARN' ? '#F87171' : '#CBD5E1' }}>{log.event}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
