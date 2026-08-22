import React, { useState, useEffect, useRef } from 'react';
import { X, Calendar, MapPin, DollarSign, CheckCircle, Save, Sparkles, AlertCircle, Clock, Users, Building, HelpCircle } from 'lucide-react';
import axios from 'axios';

export default function EventWizard({ eventIdToEdit = null, initialData = null, onClose, onSaveSuccess }) {
  const nameInputRef = useRef(null);
  const [savingDraft, setSavingDraft] = useState(false);
  const [draftSavedTime, setDraftSavedTime] = useState(null);
  const [publishErrors, setPublishErrors] = useState([]);
  const [publishedEvent, setPublishedEvent] = useState(null);

  // AI Description Drafting modal state
  const [showAiDraftModal, setShowAiDraftModal] = useState(false);
  const [aiNotes, setAiNotes] = useState('');
  const [aiDraftLoading, setAiDraftLoading] = useState(false);

  const [eventId, setEventId] = useState(eventIdToEdit);

  const [formData, setFormData] = useState({
    title: initialData?.title || initialData?.event_name || '',
    category: initialData?.category || 'Technology',
    event_type: initialData?.event_type || 'Workshop',
    description: '',
    format: 'Offline', // Offline, Online, Hybrid
    venue: initialData?.venue || '',
    address: '',
    location: initialData?.city || initialData?.location || '',
    date_str: initialData?.date_str || initialData?.date || '',
    start_time: '10:00',
    end_date_str: initialData?.date_str || initialData?.date || '',
    end_time: '16:00',
    pricing_type: 'Paid', // Paid, Free
    seating_type: 'General',
    price: 499,
    total_capacity: 100,
    max_per_customer: 4,
    ticket_types: [
      { name: 'General', price: 499, total_quantity: 100, min_per_order: 1, max_per_order: 4 }
    ],
    image_url: 'https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=800&auto=format&fit=crop&q=80',
    features: ['Certificate', 'Networking'],
    cancellation_policy: 'Standard 24-hour cancellation policy applies.',
    status: 'DRAFT'
  });

  // Autofocus Event Name on mount
  useEffect(() => {
    if (nameInputRef.current) {
      nameInputRef.current.focus();
    }
  }, []);

  // Load existing event data if editing
  useEffect(() => {
    if (eventIdToEdit) {
      axios.get(`/api/v1/events/${eventIdToEdit}`)
        .then(res => {
          const ev = res.data;
          setFormData({
            title: ev.title || '',
            category: ev.category || 'Technology',
            event_type: ev.event_type || 'Workshop',
            description: ev.description || '',
            format: ev.format || 'Offline',
            venue: ev.venue || '',
            address: ev.address || '',
            location: ev.location || '',
            date_str: ev.date_str || '',
            start_time: ev.start_time || '10:00',
            end_date_str: ev.end_date_str || ev.date_str || '',
            end_time: ev.end_time || '16:00',
            pricing_type: ev.price === 0 ? 'Free' : 'Paid',
            seating_type: ev.has_reserved_seating ? 'Reserved' : 'General',
            price: ev.price || 0,
            total_capacity: ev.total_capacity || 100,
            max_per_customer: ev.max_tickets_per_booking || 4,
            ticket_types: (ev.ticket_types && ev.ticket_types.length > 0) ? ev.ticket_types.map(t => ({
              id: t.id,
              name: t.name || 'General',
              price: t.price || 0,
              total_quantity: t.total_quantity || t.quantity || 100,
              min_per_order: t.min_per_order || 1,
              max_per_order: t.max_per_order || 4
            })) : [
              { name: 'General', price: ev.price || 0, total_quantity: ev.total_capacity || 100, min_per_order: 1, max_per_order: ev.max_tickets_per_booking || 4 }
            ],
            image_url: ev.image_url || '',
            features: ev.features || ['Certificate', 'Networking'],
            cancellation_policy: ev.cancellation_policy || 'Standard 24-hour cancellation policy applies.',
            status: ev.status || 'DRAFT'
          });
        })
        .catch(err => console.error("Failed to load event for editing", err));
    }
  }, [eventIdToEdit]);

  const handleChange = (field, value) => {
    setFormData(prev => {
      const updated = { ...prev, [field]: value };
      if (field === 'price' || field === 'total_capacity' || field === 'max_per_customer' || field === 'pricing_type') {
        const numPrice = updated.pricing_type === 'Free' ? 0 : Number(updated.price || 0);
        const numCap = Number(updated.total_capacity || 0);
        const numMax = Number(updated.max_per_customer || 4);

        if (updated.ticket_types && updated.ticket_types.length > 0) {
          updated.ticket_types = updated.ticket_types.map((t, idx) => 
            idx === 0 ? { ...t, price: numPrice, total_quantity: numCap, max_per_order: numMax } : t
          );
        }
      }
      return updated;
    });
  };

  const handleAiDraft = async () => {
    if (!aiNotes.trim()) return;
    setAiDraftLoading(true);
    try {
      const res = await axios.post('/api/v1/organizer/events/draft-description', { bullet_points: aiNotes });
      if (res.data && res.data.draft) {
        handleChange('description', res.data.draft);
        setShowAiDraftModal(false);
        setAiNotes('');
      }
    } catch (err) {
      console.error("AI draft error:", err);
    } finally {
      setAiDraftLoading(false);
    }
  };

  // Form Validation Checks
  const validateForm = () => {
    const errors = [];
    if (!formData.title?.trim()) errors.push("Event Name is required.");
    if (!formData.category?.trim()) errors.push("Category is required.");
    if (formData.format !== 'Online') {
      if (!formData.venue?.trim()) errors.push("Venue name is required for offline/hybrid events.");
      if (!formData.location?.trim()) errors.push("City is required for offline/hybrid events.");
    }
    if (!formData.date_str?.trim()) errors.push("Event Date is required.");
    if (!formData.start_time?.trim()) errors.push("Start Time is required.");
    if (!formData.end_time?.trim()) errors.push("End Time is required.");

    if (formData.start_time && formData.end_time && formData.end_time <= formData.start_time) {
      errors.push("End Time must be later than Start Time.");
    }

    if (formData.pricing_type === 'Paid' && Number(formData.price) < 0) {
      errors.push("Ticket Price cannot be negative.");
    }

    if (Number(formData.total_capacity) <= 0) {
      errors.push("Number of Tickets must be greater than 0.");
    }

    if (Number(formData.max_per_customer) < 1) {
      errors.push("Maximum tickets per person must be at least 1.");
    }

    if (Number(formData.max_per_customer) > Number(formData.total_capacity)) {
      errors.push("Maximum per person cannot exceed total ticket quantity.");
    }

    return errors;
  };

  const isTimeInvalid = Boolean(formData.start_time && formData.end_time && formData.end_time <= formData.start_time);

  const handlePublish = async () => {
    const errors = validateForm();
    if (errors.length > 0) {
      setPublishErrors(errors);
      return;
    }

    setPublishErrors([]);
    setSavingDraft(true);
    try {
      let targetId = eventId;
      const numPrice = formData.pricing_type === 'Free' ? 0 : Number(formData.price || 0);
      const numCap = Number(formData.total_capacity || 100);
      const numMax = Number(formData.max_per_customer || 4);

      const ticketTiers = (formData.ticket_types && formData.ticket_types.length > 0)
        ? formData.ticket_types.map(t => ({
            name: t.name || 'General',
            price: formData.pricing_type === 'Free' ? 0 : Number(t.price || 0),
            total_quantity: Number(t.total_quantity || numCap),
            min_per_order: 1,
            max_per_order: Number(t.max_per_order || numMax)
          }))
        : [{ name: 'General', price: numPrice, total_quantity: numCap, min_per_order: 1, max_per_order: numMax }];

      const computedTotalCapacity = ticketTiers.reduce((sum, t) => sum + Number(t.total_quantity || 0), 0);

      const payload = {
        ...formData,
        price: numPrice,
        total_capacity: computedTotalCapacity,
        location: formData.location || formData.venue || 'Bengaluru',
        ticket_types: ticketTiers,
        max_tickets_per_booking: numMax,
        status: 'DRAFT'
      };

      if (!targetId) {
        const createRes = await axios.post('/api/v1/events', payload);
        targetId = createRes.data.id;
        setEventId(targetId);
      } else {
        await axios.put(`/api/v1/events/${targetId}`, payload);
      }

      const pubRes = await axios.post(`/api/v1/events/${targetId}/publish`);
      const finalEvent = pubRes.data.event || pubRes.data;
      setPublishedEvent(finalEvent);
      if (onSaveSuccess) onSaveSuccess(finalEvent);
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (detail?.errors && Array.isArray(detail.errors)) {
        setPublishErrors(detail.errors);
      } else if (detail?.message) {
        setPublishErrors([detail.message]);
      } else if (typeof detail === 'string') {
        setPublishErrors([detail]);
      } else if (Array.isArray(detail)) {
        setPublishErrors(detail.map(e => e.msg || (typeof e === 'string' ? e : JSON.stringify(e))));
      } else if (err.message && !err.response) {
        setPublishErrors([`Failed to connect to backend (${err.message}). Please ensure the backend server is running on port 8000.`]);
      } else {
        setPublishErrors(["Failed to publish event. Please check all fields and try again."]);
      }
    } finally {
      setSavingDraft(false);
    }
  };

  // SUCCESS SCREEN VIEW
  if (publishedEvent) {
    return (
      <div style={{ position: 'fixed', inset: 0, background: 'rgba(15, 23, 42, 0.92)', backdropFilter: 'blur(16px)', zIndex: 1100, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px' }}>
        <div className="glass-panel" style={{ width: '100%', maxWidth: '580px', padding: '36px', borderRadius: '24px', textAlign: 'center', border: '1px solid rgba(16, 185, 129, 0.4)', boxShadow: '0 25px 50px -12px rgba(16, 185, 129, 0.2)' }}>
          <div style={{ width: '64px', height: '64px', borderRadius: '50%', background: 'rgba(16, 185, 129, 0.2)', border: '2px solid #10B981', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 20px auto', color: '#34D399' }}>
            <CheckCircle size={36} />
          </div>

          <h2 style={{ fontSize: '1.6rem', fontWeight: 800, color: 'white', margin: '0 0 6px 0' }}>✓ Event Published Successfully</h2>
          <h3 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#60A5FA', margin: '0 0 20px 0' }}>{publishedEvent.title}</h3>

          <div style={{ background: 'rgba(255, 255, 255, 0.05)', borderRadius: '16px', padding: '18px', marginBottom: '28px', textAlign: 'left', fontSize: '0.9rem', color: '#94A3B8', display: 'flex', flexDirection: 'column', gap: '10px', border: '1px solid rgba(255, 255, 255, 0.08)' }}>
            <div>📅 Date: <strong style={{ color: 'white' }}>{publishedEvent.date_str}</strong> ({publishedEvent.start_time} – {publishedEvent.end_time})</div>
            <div>📍 Venue & Location: <strong style={{ color: 'white' }}>{publishedEvent.venue ? `${publishedEvent.venue}, ${publishedEvent.location}` : publishedEvent.location}</strong></div>
            <div>🎟️ Total Inventory: <strong style={{ color: '#34D399' }}>{publishedEvent.total_capacity} Tickets</strong></div>
            <div>💰 Pricing: <strong style={{ color: '#60A5FA' }}>{publishedEvent.price === 0 ? 'Free Event' : `₹${publishedEvent.price} per ticket`}</strong></div>
            <div>⚡ Status: <strong style={{ color: '#10B981' }}>LIVE & PUBLISHED IN EXPLORE</strong></div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <button
              onClick={() => {
                if (onSaveSuccess) onSaveSuccess(publishedEvent, 'events');
                onClose();
              }}
              style={{ width: '100%', background: 'linear-gradient(135deg, #10B981, #059669)', color: 'white', border: 'none', padding: '14px', borderRadius: '12px', fontWeight: 700, fontSize: '0.95rem', cursor: 'pointer', minHeight: '48px', boxShadow: '0 4px 16px rgba(16, 185, 129, 0.3)' }}
            >
              View Event in Explore
            </button>
            <button
              onClick={() => {
                if (onSaveSuccess) onSaveSuccess(publishedEvent, 'organizer-studio');
                onClose();
              }}
              style={{ width: '100%', background: 'rgba(255, 255, 255, 0.08)', color: 'white', border: '1px solid var(--border-glass)', padding: '12px', borderRadius: '12px', fontWeight: 700, fontSize: '0.95rem', cursor: 'pointer', minHeight: '44px' }}
            >
              Go to Organizer Dashboard
            </button>
            <button
              onClick={() => {
                setPublishedEvent(null);
                setEventId(null);
                setFormData({
                  title: '',
                  category: 'Technology',
                  event_type: 'Workshop',
                  description: '',
                  format: 'Offline',
                  venue: '',
                  address: '',
                  location: '',
                  date_str: '',
                  start_time: '10:00',
                  end_date_str: '',
                  end_time: '16:00',
                  pricing_type: 'Paid',
                  seating_type: 'General',
                  price: 499,
                  total_capacity: 100,
                  max_per_customer: 4,
                  ticket_types: [
                    { name: 'General', price: 499, total_quantity: 100, min_per_order: 1, max_per_order: 4 }
                  ],
                  image_url: 'https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=800&auto=format&fit=crop&q=80',
                  features: ['Certificate', 'Networking'],
                  cancellation_policy: 'Standard 24-hour cancellation policy applies.',
                  status: 'DRAFT'
                });
              }}
              style={{ background: 'none', border: 'none', color: '#A78BFA', cursor: 'pointer', fontSize: '0.9rem', fontWeight: 600, marginTop: '4px' }}
            >
              + Create Another Event
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(15, 23, 42, 0.92)', backdropFilter: 'blur(14px)', zIndex: 1100, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '16px' }}>
      <div className="glass-panel" style={{ width: '100%', maxWidth: '1020px', maxHeight: '92vh', display: 'flex', flexDirection: 'column', overflow: 'hidden', border: '1px solid var(--border-glass)', boxShadow: '0 25px 50px -12px rgba(0,0,0,0.6)', borderRadius: '24px' }}>
        
        {/* Header */}
        <div style={{ padding: '22px 32px', borderBottom: '1px solid var(--border-glass)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'rgba(15, 23, 42, 0.8)' }}>
          <div>
            <h2 style={{ fontSize: '1.6rem', fontWeight: 800, color: 'white', margin: 0 }}>Create your event</h2>
            <p style={{ fontSize: '0.9rem', color: '#94A3B8', margin: '4px 0 0 0' }}>Enter the details below to publish your event and start selling tickets.</p>
          </div>
          <button onClick={onClose} style={{ background: 'rgba(255,255,255,0.08)', border: 'none', color: 'white', cursor: 'pointer', padding: '8px', borderRadius: '10px' }}>
            <X size={20} />
          </button>
        </div>

        {/* Scrollable Form Body with 2-Column Desktop Grid */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '32px' }}>
          
          {/* Publish Error Display */}
          {publishErrors.length > 0 && (
            <div style={{ background: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.4)', borderRadius: '14px', padding: '16px', marginBottom: '24px', color: '#FCA5A5' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 700, marginBottom: '6px' }}>
                <AlertCircle size={18} /> Unable to publish event
              </div>
              <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '0.88rem' }}>
                {publishErrors.map((err, idx) => <li key={idx}>{err}</li>)}
              </ul>
            </div>
          )}

          <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) 320px', gap: '28px', alignItems: 'start' }}>
            
            {/* LEFT COLUMN: FORM CARDS */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
              
              {/* SECTION 1: EVENT DETAILS */}
              <div style={{ background: 'rgba(30, 41, 59, 0.6)', borderRadius: '18px', border: '1px solid rgba(255, 255, 255, 0.08)', padding: '24px' }}>
                <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'white', margin: '0 0 16px 0', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Building size={18} color="#3B82F6" /> Event Details
                </h3>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  <div>
                    <label style={{ fontSize: '0.9rem', fontWeight: 600, color: '#E2E8F0', display: 'block', marginBottom: '6px' }}>Event Name *</label>
                    <input
                      ref={nameInputRef}
                      type="text"
                      value={formData.title}
                      onChange={(e) => handleChange('title', e.target.value)}
                      placeholder="e.g. AI Tech Workshop 2026"
                      style={{ width: '100%', background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(139, 92, 246, 0.3)', minHeight: '48px', padding: '12px 16px', fontSize: '0.95rem', borderRadius: '12px', color: 'white', outline: 'none' }}
                    />
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
                    <div>
                      <label style={{ fontSize: '0.9rem', fontWeight: 600, color: '#E2E8F0', display: 'block', marginBottom: '6px' }}>Category *</label>
                      <select
                        value={formData.category}
                        onChange={(e) => handleChange('category', e.target.value)}
                        style={{ width: '100%', background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(139, 92, 246, 0.3)', minHeight: '48px', padding: '12px 16px', fontSize: '0.95rem', borderRadius: '12px', color: 'white', outline: 'none' }}
                      >
                        <option value="Technology">Technology</option>
                        <option value="Artificial Intelligence">Artificial Intelligence</option>
                        <option value="Workshop">Workshop</option>
                        <option value="Music">Music</option>
                        <option value="Gaming">Gaming</option>
                        <option value="Sports">Sports</option>
                        <option value="Business">Business</option>
                        <option value="Education">Education</option>
                        <option value="Cultural">Cultural</option>
                        <option value="Other">Other</option>
                      </select>
                    </div>

                    <div>
                      <label style={{ fontSize: '0.9rem', fontWeight: 600, color: '#E2E8F0', display: 'block', marginBottom: '6px' }}>Event Type *</label>
                      <select
                        value={formData.event_type}
                        onChange={(e) => handleChange('event_type', e.target.value)}
                        style={{ width: '100%', background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(139, 92, 246, 0.3)', minHeight: '48px', padding: '12px 16px', fontSize: '0.95rem', borderRadius: '12px', color: 'white', outline: 'none' }}
                      >
                        <option value="Workshop">Workshop</option>
                        <option value="Conference">Conference</option>
                        <option value="Hackathon">Hackathon</option>
                        <option value="Meetup">Meetup</option>
                        <option value="Seminar">Seminar</option>
                      </select>
                    </div>
                  </div>

                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                      <label style={{ fontSize: '0.9rem', fontWeight: 600, color: '#E2E8F0' }}>Description</label>
                      <button
                        type="button"
                        onClick={() => setShowAiDraftModal(!showAiDraftModal)}
                        style={{ background: 'linear-gradient(135deg, #8B5CF6, #EC4899)', border: 'none', color: 'white', padding: '6px 12px', borderRadius: '8px', fontSize: '0.78rem', fontWeight: 700, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px' }}
                      >
                        <Sparkles size={14} /> Generate with AI
                      </button>
                    </div>

                    {showAiDraftModal && (
                      <div style={{ background: 'rgba(139, 92, 246, 0.12)', border: '1px solid rgba(139, 92, 246, 0.3)', borderRadius: '12px', padding: '12px', marginBottom: '10px' }}>
                        <p style={{ fontSize: '0.8rem', color: '#C4B5FD', margin: '0 0 8px 0', fontWeight: 600 }}>Describe key topics or bullet points for AI assistant:</p>
                        <input
                          type="text"
                          value={aiNotes}
                          onChange={(e) => setAiNotes(e.target.value)}
                          placeholder="e.g. Hands-on coding, agentic AI, React & FastAPI"
                          style={{ width: '100%', background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(255,255,255,0.1)', padding: '8px 12px', fontSize: '0.85rem', borderRadius: '8px', color: 'white', marginBottom: '8px' }}
                        />
                        <button
                          type="button"
                          disabled={aiDraftLoading || !aiNotes.trim()}
                          onClick={handleAiDraft}
                          style={{ background: '#8B5CF6', color: 'white', border: 'none', padding: '6px 12px', borderRadius: '6px', fontSize: '0.8rem', fontWeight: 700, cursor: 'pointer' }}
                        >
                          {aiDraftLoading ? 'Generating...' : 'Apply AI Description'}
                        </button>
                      </div>
                    )}

                    <textarea
                      rows={3}
                      value={formData.description}
                      onChange={(e) => handleChange('description', e.target.value)}
                      placeholder="Tell attendees what your event is about, who it is for, and what they can expect."
                      style={{ width: '100%', background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(139, 92, 246, 0.3)', padding: '12px 16px', fontSize: '0.95rem', borderRadius: '12px', color: 'white', outline: 'none', resize: 'vertical' }}
                    />
                  </div>
                </div>
              </div>

              {/* SECTION 2: LOCATION & SCHEDULE */}
              <div style={{ background: 'rgba(30, 41, 59, 0.6)', borderRadius: '18px', border: '1px solid rgba(255, 255, 255, 0.08)', padding: '24px' }}>
                <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'white', margin: '0 0 16px 0', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <MapPin size={18} color="#10B981" /> Location & Schedule
                </h3>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  <div>
                    <label style={{ fontSize: '0.9rem', fontWeight: 600, color: '#E2E8F0', display: 'block', marginBottom: '8px' }}>Event Format</label>
                    <div style={{ display: 'flex', gap: '18px' }}>
                      {['Offline', 'Online', 'Hybrid'].map((fmt) => (
                        <label key={fmt} style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '0.9rem', color: 'white', fontWeight: 600 }}>
                          <input
                            type="radio"
                            name="format"
                            checked={formData.format === fmt}
                            onChange={() => handleChange('format', fmt)}
                            style={{ accentColor: '#10B981', width: '16px', height: '16px' }}
                          />
                          {fmt}
                        </label>
                      ))}
                    </div>
                  </div>

                  {formData.format !== 'Online' && (
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
                      <div>
                        <label style={{ fontSize: '0.9rem', fontWeight: 600, color: '#E2E8F0', display: 'block', marginBottom: '6px' }}>Venue Name *</label>
                        <input
                          type="text"
                          value={formData.venue}
                          onChange={(e) => handleChange('venue', e.target.value)}
                          placeholder="e.g. AJIET Main Auditorium"
                          style={{ width: '100%', background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(139, 92, 246, 0.3)', minHeight: '48px', padding: '12px 16px', fontSize: '0.95rem', borderRadius: '12px', color: 'white', outline: 'none' }}
                        />
                      </div>
                      <div>
                        <label style={{ fontSize: '0.9rem', fontWeight: 600, color: '#E2E8F0', display: 'block', marginBottom: '6px' }}>City *</label>
                        <input
                          type="text"
                          value={formData.location}
                          onChange={(e) => handleChange('location', e.target.value)}
                          placeholder="e.g. Mangaluru"
                          style={{ width: '100%', background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(139, 92, 246, 0.3)', minHeight: '48px', padding: '12px 16px', fontSize: '0.95rem', borderRadius: '12px', color: 'white', outline: 'none' }}
                        />
                      </div>
                    </div>
                  )}

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '14px' }}>
                    <div>
                      <label style={{ fontSize: '0.9rem', fontWeight: 600, color: '#E2E8F0', display: 'block', marginBottom: '6px' }}>Event Date *</label>
                      <input
                        type="date"
                        value={formData.date_str}
                        onChange={(e) => handleChange('date_str', e.target.value)}
                        style={{ width: '100%', background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(139, 92, 246, 0.3)', minHeight: '48px', padding: '12px 14px', fontSize: '0.9rem', borderRadius: '12px', color: 'white', outline: 'none' }}
                      />
                    </div>
                    <div>
                      <label style={{ fontSize: '0.9rem', fontWeight: 600, color: '#E2E8F0', display: 'block', marginBottom: '6px' }}>Start Time *</label>
                      <input
                        type="time"
                        value={formData.start_time}
                        onChange={(e) => handleChange('start_time', e.target.value)}
                        style={{ width: '100%', background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(139, 92, 246, 0.3)', minHeight: '48px', padding: '12px 14px', fontSize: '0.9rem', borderRadius: '12px', color: 'white', outline: 'none' }}
                      />
                    </div>
                    <div>
                      <label style={{ fontSize: '0.9rem', fontWeight: 600, color: '#E2E8F0', display: 'block', marginBottom: '6px' }}>End Time *</label>
                      <input
                        type="time"
                        value={formData.end_time}
                        onChange={(e) => handleChange('end_time', e.target.value)}
                        style={{ width: '100%', background: isTimeInvalid ? 'rgba(239, 68, 68, 0.2)' : 'rgba(15, 23, 42, 0.8)', border: isTimeInvalid ? '1px solid #EF4444' : '1px solid rgba(139, 92, 246, 0.3)', minHeight: '48px', padding: '12px 14px', fontSize: '0.9rem', borderRadius: '12px', color: 'white', outline: 'none' }}
                      />
                    </div>
                  </div>

                  {isTimeInvalid && (
                    <div style={{ color: '#F87171', fontSize: '0.85rem', fontWeight: 600, marginTop: '-6px' }}>
                      ⚠️ End time must be later than start time.
                    </div>
                  )}
                </div>
              </div>

              {/* SECTION 3: TICKETS & PRICING */}
              <div style={{ background: 'rgba(30, 41, 59, 0.6)', borderRadius: '18px', border: '1px solid rgba(255, 255, 255, 0.08)', padding: '24px' }}>
                <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'white', margin: '0 0 16px 0', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <DollarSign size={18} color="#F59E0B" /> Ticket Pricing & Quantity
                </h3>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  <div>
                    <label style={{ fontSize: '0.9rem', fontWeight: 600, color: '#E2E8F0', display: 'block', marginBottom: '8px' }}>Pricing Type</label>
                    <div style={{ display: 'flex', gap: '20px' }}>
                      {['Paid', 'Free'].map((pt) => (
                        <label key={pt} style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '0.9rem', color: 'white', fontWeight: 600 }}>
                          <input
                            type="radio"
                            name="pricing_type"
                            checked={formData.pricing_type === pt}
                            onChange={() => handleChange('pricing_type', pt)}
                            style={{ accentColor: '#F59E0B', width: '16px', height: '16px' }}
                          />
                          {pt} Event
                        </label>
                      ))}
                    </div>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '14px' }}>
                    <div>
                      <label style={{ fontSize: '0.9rem', fontWeight: 600, color: '#E2E8F0', display: 'block', marginBottom: '6px' }}>Ticket Price (₹) *</label>
                      <input
                        type="number"
                        min="0"
                        step="1"
                        disabled={formData.pricing_type === 'Free'}
                        value={formData.pricing_type === 'Free' ? 0 : formData.price}
                        onChange={(e) => handleChange('price', e.target.value)}
                        placeholder="299"
                        style={{ width: '100%', background: formData.pricing_type === 'Free' ? 'rgba(255,255,255,0.05)' : 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(139, 92, 246, 0.3)', minHeight: '48px', padding: '12px 16px', fontSize: '0.95rem', borderRadius: '12px', color: 'white', outline: 'none' }}
                      />
                    </div>

                    <div>
                      <label style={{ fontSize: '0.9rem', fontWeight: 600, color: '#E2E8F0', display: 'block', marginBottom: '6px' }}>Number of Tickets *</label>
                      <input
                        type="number"
                        min="1"
                        value={formData.total_capacity}
                        onChange={(e) => handleChange('total_capacity', e.target.value)}
                        placeholder="150"
                        style={{ width: '100%', background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(139, 92, 246, 0.3)', minHeight: '48px', padding: '12px 16px', fontSize: '0.95rem', borderRadius: '12px', color: 'white', outline: 'none' }}
                      />
                    </div>

                    <div>
                      <label style={{ fontSize: '0.9rem', fontWeight: 600, color: '#E2E8F0', display: 'block', marginBottom: '6px' }}>Max Tickets / Person *</label>
                      <input
                        type="number"
                        min="1"
                        value={formData.max_per_customer}
                        onChange={(e) => handleChange('max_per_customer', e.target.value)}
                        placeholder="4"
                        style={{ width: '100%', background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(139, 92, 246, 0.3)', minHeight: '48px', padding: '12px 16px', fontSize: '0.95rem', borderRadius: '12px', color: 'white', outline: 'none' }}
                      />
                    </div>
                  </div>
                </div>
              </div>

            </div>

            {/* RIGHT COLUMN: LIVE EVENT SUMMARY CARD */}
            <div style={{ position: 'sticky', top: 0 }}>
              <div style={{ background: 'linear-gradient(145deg, rgba(30, 41, 59, 0.9), rgba(15, 23, 42, 0.95))', borderRadius: '20px', border: '1px solid rgba(139, 92, 246, 0.3)', padding: '24px', boxShadow: '0 12px 32px rgba(0,0,0,0.4)' }}>
                <span style={{ fontSize: '0.72rem', fontWeight: 800, color: '#A78BFA', textTransform: 'uppercase', letterSpacing: '0.5px', display: 'block', marginBottom: '12px' }}>
                  ✨ EVENT SUMMARY PREVIEW
                </span>

                <h4 style={{ fontSize: '1.2rem', fontWeight: 800, color: 'white', margin: '0 0 6px 0', lineHeight: 1.3 }}>
                  {formData.title.trim() || 'My College Tech Fest'}
                </h4>

                <div style={{ fontSize: '0.85rem', color: '#60A5FA', fontWeight: 700, marginBottom: '16px' }}>
                  {formData.category || 'Technology'} • {formData.event_type || 'Workshop'} ({formData.format})
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '0.85rem', color: '#94A3B8', borderTop: '1px solid rgba(255, 255, 255, 0.08)', borderBottom: '1px solid rgba(255, 255, 255, 0.08)', padding: '14px 0', marginBottom: '18px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <MapPin size={16} color="#34D399" />
                    <span>{formData.venue ? `${formData.venue}, ${formData.location || 'Mangaluru'}` : (formData.location || 'Mangaluru')}</span>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Calendar size={16} color="#60A5FA" />
                    <span>{formData.date_str || '2026-09-30'} ({formData.start_time} – {formData.end_time})</span>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Users size={16} color="#F59E0B" />
                    <span>{formData.total_capacity || 150} Total Tickets ({formData.max_per_customer || 4} max/order)</span>
                  </div>
                </div>

                <div style={{ background: 'rgba(255, 255, 255, 0.04)', borderRadius: '12px', padding: '14px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div>
                    <span style={{ fontSize: '0.78rem', color: '#CBD5E1', display: 'block' }}>General Admission</span>
                    <strong style={{ fontSize: '1.25rem', color: '#34D399', fontWeight: 800 }}>
                      {formData.pricing_type === 'Free' ? 'FREE' : `₹${formData.price || 299}`}
                    </strong>
                  </div>
                  <span style={{ fontSize: '0.8rem', background: 'rgba(16, 185, 129, 0.2)', color: '#34D399', padding: '4px 10px', borderRadius: '12px', fontWeight: 700 }}>
                    {formData.total_capacity || 150} Available
                  </span>
                </div>
              </div>
            </div>

          </div>
        </div>

        {/* Footer Actions Bar */}
        <div style={{ padding: '20px 32px', borderTop: '1px solid var(--border-glass)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'rgba(15, 23, 42, 0.95)' }}>
          <button
            type="button"
            onClick={onClose}
            style={{ background: 'rgba(255, 255, 255, 0.08)', color: '#CBD5E1', border: '1px solid var(--border-glass)', padding: '12px 24px', borderRadius: '12px', fontWeight: 700, fontSize: '0.95rem', cursor: 'pointer', minHeight: '48px' }}
          >
            Cancel
          </button>

          <button
            type="button"
            disabled={savingDraft || isTimeInvalid}
            onClick={handlePublish}
            style={{
              background: savingDraft || isTimeInvalid ? 'rgba(16, 185, 129, 0.4)' : 'linear-gradient(135deg, #10B981, #059669)',
              color: 'white',
              border: 'none',
              padding: '12px 28px',
              borderRadius: '12px',
              fontWeight: 800,
              fontSize: '0.95rem',
              cursor: savingDraft || isTimeInvalid ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              boxShadow: '0 4px 16px rgba(16, 185, 129, 0.3)',
              minHeight: '48px',
              minWidth: '180px',
              justifyContent: 'center'
            }}
          >
            {savingDraft ? 'Publishing Event...' : '🚀 Publish Event'}
          </button>
        </div>

      </div>
    </div>
  );
}
