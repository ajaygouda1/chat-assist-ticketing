import React, { useState, useEffect } from 'react';
import { Plus, Edit3, Copy, XCircle, Users, QrCode, Calendar, MapPin, DollarSign, RefreshCw, Eye, AlertCircle, Lock } from 'lucide-react';
import axios from 'axios';
import EventWizard from './EventWizard';
import { useAuth } from '../../context/AuthContext';


export default function MyEvents({ onNavigateToScanner }) {
  const [activeTab, setActiveTab] = useState('ALL'); // DRAFT, PUBLISHED, PAST, CANCELLED, ALL
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isWizardOpen, setIsWizardOpen] = useState(false);
  const [editingEventId, setEditingEventId] = useState(null);
  
  // Bookings Inspection Modal
  const [inspectBookingsEvent, setInspectBookingsEvent] = useState(null);
  const [eventBookings, setEventBookings] = useState([]);

  useEffect(() => {
    fetchOrganizerEvents();
  }, [activeTab]);

  const fetchOrganizerEvents = async () => {
    setLoading(true);
    try {
      const url = activeTab === 'ALL' 
        ? '/api/v1/organizer/events' 
        : `/api/v1/organizer/events?status=${activeTab}`;
      const res = await axios.get(url);
      setEvents(res.data);
    } catch (err) {
      console.error("Error fetching organizer events", err);
    } finally {
      setLoading(false);
    }
  };

  const handleDuplicate = async (eventId) => {
    try {
      await axios.post(`/api/v1/events/${eventId}/duplicate`);
      fetchOrganizerEvents();
    } catch (err) {
      alert("Failed to duplicate event");
    }
  };

  const handleCancelEvent = async (eventId) => {
    if (!window.confirm("Are you sure you want to cancel this event? Attendees will be notified.")) return;
    try {
      await axios.post(`/api/v1/events/${eventId}/cancel`);
      fetchOrganizerEvents();
    } catch (err) {
      alert("Failed to cancel event");
    }
  };

  const handleViewBookings = async (ev) => {
    setInspectBookingsEvent(ev);
    try {
      const res = await axios.get(`/api/v1/organizer/events/${ev.id}/bookings`);
      setEventBookings(res.data.bookings || []);
    } catch (err) {
      setEventBookings([]);
    }
  };

  const filteredEvents = events.filter(e => {
    if (activeTab === 'ALL') return true;
    return e.status === activeTab;
  });

  return (
    <div style={{ padding: '0 24px 40px 24px' }}>
      
      {/* Header Bar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'white' }}>Website Event Organizer Studio</h2>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>Manage event listings, save-as-draft wizard, attendee bookings, & gate check-ins</p>
        </div>

        <div style={{ display: 'flex', gap: '12px' }}>
          <button
            onClick={() => fetchOrganizerEvents()}
            style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border-glass)', color: 'var(--text-muted)', padding: '10px 14px', borderRadius: '10px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            <RefreshCw size={16} /> Refresh
          </button>

          <button
            onClick={() => { setEditingEventId(null); setIsWizardOpen(true); }}
            className="gradient-btn"
            style={{ padding: '10px 20px', fontSize: '0.9rem' }}
          >
            <Plus size={18} /> + Create Event (Wizard)
          </button>
        </div>
      </div>

      {/* Tabs Bar (§45a: Draft / Published / Past / Cancelled) */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '20px', borderBottom: '1px solid var(--border-glass)', pb: '12px' }}>
        {[
          { key: 'ALL', label: 'All Events' },
          { key: 'DRAFT', label: 'Drafts' },
          { key: 'PUBLISHED', label: 'Published' },
          { key: 'PAST', label: 'Past Events' },
          { key: 'CANCELLED', label: 'Cancelled' }
        ].map(tab => {
          const isActive = activeTab === tab.key;
          const count = events.filter(e => tab.key === 'ALL' || e.status === tab.key).length;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              style={{
                background: isActive ? 'rgba(59, 130, 246, 0.2)' : 'transparent',
                color: isActive ? '#60A5FA' : 'var(--text-muted)',
                border: 'none',
                borderBottom: isActive ? '2px solid #3B82F6' : '2px solid transparent',
                padding: '10px 16px',
                borderRadius: '8px 8px 0 0',
                cursor: 'pointer',
                fontWeight: 600,
                fontSize: '0.875rem',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}
            >
              <span>{tab.label}</span>
              <span style={{ background: isActive ? 'rgba(59, 130, 246, 0.4)' : 'rgba(255,255,255,0.08)', padding: '2px 8px', borderRadius: '12px', fontSize: '0.75rem' }}>
                {count}
              </span>
            </button>
          );
        })}
      </div>

      {/* Events Table / List */}
      {loading ? (
        <div className="glass-panel" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
          Loading organizer events...
        </div>
      ) : filteredEvents.length === 0 ? (
        <div className="glass-panel" style={{ padding: '60px', textAlign: 'center', color: 'var(--text-muted)' }}>
          <AlertCircle size={48} style={{ opacity: 0.3, margin: '0 auto 12px auto' }} />
          <h3 style={{ fontSize: '1.1rem', color: 'white', marginBottom: '6px' }}>No events found in '{activeTab}' category</h3>
          <p style={{ fontSize: '0.85rem' }}>Click "+ Create Event (Wizard)" to create a new draft event.</p>
        </div>
      ) : (
        <div className="glass-panel" style={{ padding: '0', overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.875rem' }}>
            <thead>
              <tr style={{ background: 'rgba(0,0,0,0.3)', borderBottom: '1px solid var(--border-glass)', color: 'var(--text-muted)' }}>
                <th style={{ padding: '16px 20px' }}>Event & Title</th>
                <th style={{ padding: '16px 20px' }}>Date & Venue</th>
                <th style={{ padding: '16px 20px' }}>Tickets Sold / Capacity</th>
                <th style={{ padding: '16px 20px' }}>Revenue So Far</th>
                <th style={{ padding: '16px 20px' }}>Status</th>
                <th style={{ padding: '16px 20px', textAlign: 'right' }}>Quick Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredEvents.map((ev) => {
                const canModify = !user || user.role === 'super_admin' || user.role === 'admin' || !ev.organizer_id || ev.organizer_id === user.id;

                return (
                  <tr key={ev.id} style={{ borderBottom: '1px solid var(--border-glass)' }}>
                    <td style={{ padding: '16px 20px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <img
                          src={ev.image_url || "https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=100&auto=format&fit=crop&q=80"}
                          alt={ev.title}
                          style={{ width: '48px', height: '48px', borderRadius: '8px', objectFit: 'cover' }}
                        />
                        <div>
                          <div style={{ fontWeight: 700, color: 'white', fontSize: '0.95rem' }}>{ev.title}</div>
                          <span style={{ fontSize: '0.75rem', color: '#60A5FA' }}>{ev.category}</span>
                        </div>
                      </div>
                    </td>
                    <td style={{ padding: '16px 20px', color: 'var(--text-muted)' }}>
                      <div style={{ color: 'white', fontWeight: 500 }}>{ev.date_str}</div>
                      <div style={{ fontSize: '0.75rem' }}>{ev.location}</div>
                    </td>
                    <td style={{ padding: '16px 20px' }}>
                      <div style={{ fontWeight: 700, color: 'white' }}>
                        {ev.tickets_sold} / {ev.total_capacity}
                      </div>
                      <div style={{ width: '100px', height: '6px', background: 'rgba(255,255,255,0.1)', borderRadius: '3px', marginTop: '4px', overflow: 'hidden' }}>
                        <div style={{
                          width: `${Math.min(100, ((ev.tickets_sold || 0) / (ev.total_capacity || 1)) * 100)}%`,
                          height: '100%',
                          background: 'linear-gradient(90deg, #3B82F6, #10B981)'
                        }} />
                      </div>
                    </td>
                    <td style={{ padding: '16px 20px', fontWeight: 800, color: '#34D399' }}>
                      ₹{ev.revenue_so_far?.toLocaleString() || '0'}
                    </td>
                    <td style={{ padding: '16px 20px' }}>
                      <span className={`badge ${
                        ev.status === 'PUBLISHED' ? 'badge-grounded' :
                        ev.status === 'DRAFT' ? 'badge' :
                        ev.status === 'CANCELLED' ? '' : 'badge'
                      }`} style={{
                        background: ev.status === 'DRAFT' ? 'rgba(234, 179, 8, 0.2)' : ev.status === 'CANCELLED' ? 'rgba(239, 68, 68, 0.2)' : undefined,
                        color: ev.status === 'DRAFT' ? '#FACC15' : ev.status === 'CANCELLED' ? '#F87171' : undefined,
                        border: ev.status === 'DRAFT' ? '1px solid #FACC15' : ev.status === 'CANCELLED' ? '1px solid #F87171' : undefined
                      }}>
                        {ev.status}
                      </span>
                    </td>
                    <td style={{ padding: '16px 20px', textAlign: 'right' }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '8px' }}>
                        {canModify ? (
                          <>
                            <button
                              onClick={() => { setEditingEventId(ev.id); setIsWizardOpen(true); }}
                              title="Edit Event Wizard"
                              style={{ background: 'rgba(59, 130, 246, 0.15)', color: '#60A5FA', border: 'none', padding: '6px 10px', borderRadius: '6px', cursor: 'pointer', fontSize: '0.75rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '4px' }}
                            >
                              <Edit3 size={14} /> Edit
                            </button>

                            <button
                              onClick={() => handleDuplicate(ev.id)}
                              title="Duplicate as Draft"
                              style={{ background: 'rgba(255, 255, 255, 0.08)', color: 'white', border: 'none', padding: '6px 10px', borderRadius: '6px', cursor: 'pointer', fontSize: '0.75rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '4px' }}
                            >
                              <Copy size={14} /> Duplicate
                            </button>
                          </>
                        ) : (
                          <span title="Only event owner or super_admin can edit" style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px', background: 'rgba(255,255,255,0.05)', padding: '4px 8px', borderRadius: '6px' }}>
                            <Lock size={12} color="#F87171" /> Locked (Other Organizer)
                          </span>
                        )}

                        <button
                          onClick={() => handleViewBookings(ev)}
                          title="View Bookings"
                          style={{ background: 'rgba(16, 185, 129, 0.15)', color: '#34D399', border: 'none', padding: '6px 10px', borderRadius: '6px', cursor: 'pointer', fontSize: '0.75rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '4px' }}
                        >
                          <Users size={14} /> Bookings
                        </button>

                        {onNavigateToScanner && (
                          <button
                            onClick={() => onNavigateToScanner(ev.id)}
                            title="Gate Check-In"
                            style={{ background: 'rgba(139, 92, 246, 0.15)', color: '#C084FC', border: 'none', padding: '6px 10px', borderRadius: '6px', cursor: 'pointer', fontSize: '0.75rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '4px' }}
                          >
                            <QrCode size={14} /> Scan
                          </button>
                        )}

                        {canModify && ev.status !== 'CANCELLED' && (
                          <button
                            onClick={() => handleCancelEvent(ev.id)}
                            title="Cancel Event"
                            style={{ background: 'rgba(239, 68, 68, 0.15)', color: '#F87171', border: 'none', padding: '6px', borderRadius: '6px', cursor: 'pointer' }}
                          >
                            <XCircle size={14} />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>

          </table>
        </div>
      )}

      {/* Event Wizard Modal */}
      {isWizardOpen && (
        <EventWizard
          eventIdToEdit={editingEventId}
          onClose={() => setIsWizardOpen(false)}
          onSaveSuccess={() => fetchOrganizerEvents()}
        />
      )}

      {/* Bookings Modal */}
      {inspectBookingsEvent && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.8)', backdropFilter: 'blur(8px)', zIndex: 1200, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px' }}>
          <div className="glass-panel" style={{ width: '100%', maxWidth: '650px', padding: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div>
                <h3 style={{ fontSize: '1.2rem', fontWeight: 800, color: 'white' }}>Attendee Bookings</h3>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{inspectBookingsEvent.title}</p>
              </div>
              <button onClick={() => setInspectBookingsEvent(null)} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>✕</button>
            </div>

            {eventBookings.length === 0 ? (
              <p style={{ color: 'var(--text-muted)', padding: '20px 0', textAlign: 'center' }}>No bookings for this event yet.</p>
            ) : (
              <div style={{ maxHeight: '350px', overflowY: 'auto' }}>
                <table style={{ width: '100%', fontSize: '0.85rem', color: 'white' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid var(--border-glass)', color: 'var(--text-muted)' }}>
                      <th style={{ padding: '8px' }}>Ticket #</th>
                      <th style={{ padding: '8px' }}>Amount</th>
                      <th style={{ padding: '8px' }}>Status</th>
                      <th style={{ padding: '8px' }}>Checked In At</th>
                    </tr>
                  </thead>
                  <tbody>
                    {eventBookings.map(b => (
                      <tr key={b.ticket_id} style={{ borderBottom: '1px solid var(--border-glass)' }}>
                        <td style={{ padding: '8px', fontWeight: 600, color: '#60A5FA' }}>{b.ticket_number}</td>
                        <td style={{ padding: '8px' }}>₹{b.price_paid}</td>
                        <td style={{ padding: '8px' }}><span className="badge badge-grounded">{b.status}</span></td>
                        <td style={{ padding: '8px', color: 'var(--text-muted)' }}>{b.checked_in_at || 'Not yet'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

    </div>
  );
}
