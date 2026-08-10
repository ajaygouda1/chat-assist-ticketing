import React, { useState, useEffect } from 'react';
import { DollarSign, ShieldCheck, UserPlus, CheckCircle, Clock } from 'lucide-react';
import axios from 'axios';

export default function OrganizerPayouts() {
  const [payouts, setPayouts] = useState([]);
  const [staffEmail, setStaffEmail] = useState('');
  const [invited, setInvited] = useState(false);

  useEffect(() => {
    fetchPayouts();
  }, []);

  const fetchPayouts = async () => {
    try {
      const res = await axios.get('/api/v1/organizer/payouts');
      setPayouts(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const handleInviteStaff = async (e) => {
    e.preventDefault();
    if (!staffEmail) return;
    try {
      await axios.post('/api/v1/staff/invite', { staff_email: staffEmail, permissions: ['scan_tickets'] });
      setInvited(true);
      setStaffEmail('');
      setTimeout(() => setInvited(false), 3000);
    } catch (err) {
      alert('Failed to invite staff');
    }
  };

  return (
    <div style={{ padding: '0 24px 40px 24px' }}>
      <div style={{ marginBottom: '24px' }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'white' }}>Organizer Dashboard & Automated Escrow Payouts</h2>
        <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>Funds held in escrow released 48h post-event to verified bank account</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px', marginBottom: '32px' }}>
        <div className="glass-panel" style={{ padding: '20px' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Total Escrow Released</span>
          <h3 style={{ fontSize: '1.75rem', fontWeight: 800, color: '#34D399' }}>₹14,500.00</h3>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '8px', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <CheckCircle size={12} color="#34D399" /> Direct Deposit to HDFC Bank ****9821
          </p>
        </div>

        <div className="glass-panel" style={{ padding: '20px' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Pending Escrow Hold</span>
          <h3 style={{ fontSize: '1.75rem', fontWeight: 800, color: '#60A5FA' }}>₹3,299.00</h3>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '8px', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <Clock size={12} color="#60A5FA" /> Scheduled auto-release in 36 hours
          </p>
        </div>
      </div>

      {/* Staff Sub-Accounts Invite Section */}
      <div className="glass-panel" style={{ padding: '24px', maxWidth: '600px' }}>
        <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'white', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <UserPlus size={18} color="#A78BFA" /> Invite Event Staff Sub-Account
        </h3>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '16px' }}>
          Grant scoped permissions (e.g. "Can scan QR tickets at door" vs "Can access revenue")
        </p>

        <form onSubmit={handleInviteStaff} style={{ display: 'flex', gap: '10px' }}>
          <input
            type="email"
            placeholder="staff.email@event.com"
            value={staffEmail}
            onChange={(e) => setStaffEmail(e.target.value)}
            style={{ flex: 1, background: 'rgba(15, 23, 42, 0.6)', border: '1px solid var(--border-glass)', borderRadius: '10px', padding: '10px 14px', color: 'white', outline: 'none' }}
          />
          <button type="submit" className="gradient-btn">Invite Staff</button>
        </form>
        {invited && <p style={{ color: '#34D399', fontSize: '0.8rem', marginTop: '8px' }}>Staff sub-account invite sent!</p>}
      </div>
    </div>
  );
}
