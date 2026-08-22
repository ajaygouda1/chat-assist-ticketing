import React, { useState, useRef, useEffect } from 'react';
import { Building, MapPin, DollarSign, Calendar, Users, CheckCircle, AlertCircle, Sparkles } from 'lucide-react';
import axios from 'axios';

export default function CreateEventPage({ onNavigateToExplore, onNavigateToDashboard }) {
  const nameInputRef = useRef(null);

  const [form, setForm] = useState({
    name: '',
    category: 'Technology',
    event_type: 'Workshop',
    description: '',
    format: 'Offline', // Offline, Online, Hybrid
    venue: '',
    city: '',
    date: '',
    startTime: '09:30',
    endTime: '16:30',
    pricingType: 'paid', // paid, free
    price: '299',
    totalQuantity: '150',
    maxPerOrder: 5
  });

  const [publishing, setPublishing] = useState(false);
  const [errors, setErrors] = useState([]);
  const [publishedEvent, setPublishedEvent] = useState(null);

  useEffect(() => {
    if (nameInputRef.current) {
      nameInputRef.current.focus();
    }
  }, []);

  const handleChange = (field, value) => {
    setForm(prev => ({ ...prev, [field]: value }));
  };

  const isTimeInvalid = Boolean(form.startTime && form.endTime && form.endTime <= form.startTime);

  const validate = () => {
    const errs = [];
    if (!form.name.trim()) errs.push("Event Name is required.");
    if (!form.category.trim()) errs.push("Category is required.");
    if (form.format !== 'Online') {
      if (!form.venue.trim()) errs.push("Venue is required for offline/hybrid events.");
      if (!form.city.trim()) errs.push("City is required for offline/hybrid events.");
    }
    if (!form.date.trim()) errs.push("Event Date is required.");
    if (!form.startTime.trim()) errs.push("Start Time is required.");
    if (!form.endTime.trim()) errs.push("End Time is required.");

    if (form.startTime && form.endTime && form.endTime <= form.startTime) {
      errs.push("End time must be later than start time.");
    }

    if (form.pricingType === 'paid' && Number(form.price) < 0) {
      errs.push("Ticket price cannot be negative.");
    }

    if (Number(form.totalQuantity) <= 0) {
      errs.push("Number of tickets must be greater than 0.");
    }

    if (Number(form.maxPerOrder) <= 0) {
      errs.push("Maximum tickets per person must be at least 1.");
    }

    if (Number(form.maxPerOrder) > Number(form.totalQuantity)) {
      errs.push("Maximum per person cannot exceed total number of tickets.");
    }

    return errs;
  };

  const handlePublish = async () => {
    const errs = validate();
    if (errs.length > 0) {
      setErrors(errs);
      return;
    }

    setErrors([]);
    setPublishing(true);

    try {
      const numPrice = form.pricingType === 'free' ? 0 : Number(form.price || 0);
      const numTickets = Number(form.totalQuantity || 150);
      const numMax = Number(form.maxPerOrder || 5);

      const payload = {
        title: form.name,
        category: form.category,
        event_type: form.event_type,
        description: form.description,
        format: form.format,
        venue: form.venue,
        location: form.city || form.venue,
        date_str: form.date,
        start_time: form.startTime,
        end_time: form.endTime,
        price: numPrice,
        total_capacity: numTickets,
        max_tickets_per_booking: numMax,
        status: 'DRAFT',
        ticket_types: [
          {
            name: 'General',
            price: numPrice,
            total_quantity: numTickets,
            min_per_order: 1,
            max_per_order: numMax
          }
        ]
      };

      const createRes = await axios.post('/api/v1/events', payload);
      const targetId = createRes.data.id;

      const pubRes = await axios.post(`/api/v1/events/${targetId}/publish`);
      const finalEvent = pubRes.data.event || pubRes.data;
      setPublishedEvent(finalEvent);
    } catch (err) {
      if (err.response?.data?.detail?.errors) {
        setErrors(err.response.data.detail.errors);
      } else if (err.response?.data?.detail?.message) {
        setErrors([err.response.data.detail.message]);
      } else {
        setErrors(["Failed to publish event. Please check backend connection."]);
      }
    } finally {
      setPublishing(false);
    }
  };

  // SUCCESS PAGE VIEW
  if (publishedEvent) {
    return (
      <div style={{ maxWidth: '640px', margin: '40px auto', padding: '0 24px' }}>
        <div className="glass-panel" style={{ padding: '40px', borderRadius: '24px', textAlign: 'center', border: '1px solid rgba(16, 185, 129, 0.4)', boxShadow: '0 25px 50px -12px rgba(16, 185, 129, 0.2)' }}>
          <div style={{ width: '64px', height: '64px', borderRadius: '50%', background: 'rgba(16, 185, 129, 0.2)', border: '2px solid #10B981', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 20px auto', color: '#34D399' }}>
            <CheckCircle size={36} />
          </div>

          <h2 style={{ fontSize: '1.75rem', fontWeight: 800, color: 'white', margin: '0 0 8px 0' }}>✓ Event Published Successfully</h2>
          <h3 style={{ fontSize: '1.3rem', fontWeight: 700, color: '#60A5FA', margin: '0 0 24px 0' }}>{publishedEvent.title}</h3>

          <div style={{ background: 'rgba(255, 255, 255, 0.05)', borderRadius: '16px', padding: '20px', marginBottom: '32px', textAlign: 'left', fontSize: '0.95rem', color: '#94A3B8', display: 'flex', flexDirection: 'column', gap: '10px', border: '1px solid rgba(255, 255, 255, 0.08)' }}>
            <div>🎟️ Created Inventory: <strong style={{ color: '#34D399' }}>{publishedEvent.total_capacity} tickets created</strong></div>
            <div>💰 Pricing: <strong style={{ color: '#60A5FA' }}>{publishedEvent.price === 0 ? 'Free Event' : `₹${publishedEvent.price} per ticket`}</strong></div>
            <div>📍 Venue & City: <strong style={{ color: 'white' }}>{publishedEvent.venue ? `${publishedEvent.venue}, ${publishedEvent.location}` : publishedEvent.location}</strong></div>
            <div>📅 Date & Time: <strong style={{ color: 'white' }}>{publishedEvent.date_str} ({publishedEvent.start_time} – {publishedEvent.end_time})</strong></div>
          </div>

          <div style={{ display: 'flex', gap: '14px' }}>
            <button
              onClick={() => onNavigateToExplore && onNavigateToExplore(publishedEvent)}
              style={{ flex: 1, background: 'linear-gradient(135deg, #10B981, #059669)', color: 'white', border: 'none', padding: '14px', borderRadius: '12px', fontWeight: 700, fontSize: '0.95rem', cursor: 'pointer', minHeight: '48px', boxShadow: '0 4px 16px rgba(16, 185, 129, 0.3)' }}
            >
              View Event in Explore
            </button>
            <button
              onClick={() => {
                setPublishedEvent(null);
                setForm({
                  name: '',
                  category: 'Technology',
                  event_type: 'Workshop',
                  description: '',
                  format: 'Offline',
                  venue: '',
                  city: '',
                  date: '',
                  startTime: '09:30',
                  endTime: '16:30',
                  pricingType: 'paid',
                  price: '299',
                  totalQuantity: '150',
                  maxPerOrder: 5
                });
              }}
              style={{ flex: 1, background: 'rgba(255, 255, 255, 0.08)', color: 'white', border: '1px solid var(--border-glass)', padding: '14px', borderRadius: '12px', fontWeight: 700, fontSize: '0.95rem', cursor: 'pointer', minHeight: '48px' }}
            >
              + Create Another Event
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto', padding: '40px 24px' }}>
      
      {/* Page Header */}
      <div style={{ marginBottom: '32px' }}>
        <h1 style={{ fontSize: '1.9rem', fontWeight: 800, color: 'white', margin: '0 0 6px 0' }}>CREATE YOUR EVENT</h1>
        <p style={{ fontSize: '0.95rem', color: '#94A3B8', margin: 0 }}>Enter event details and ticket inventory below to publish your event live.</p>
      </div>

      {/* Errors Banner */}
      {errors.length > 0 && (
        <div style={{ background: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.4)', borderRadius: '14px', padding: '16px 20px', marginBottom: '28px', color: '#FCA5A5' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 700, marginBottom: '6px' }}>
            <AlertCircle size={18} /> Unable to publish event
          </div>
          <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '0.9rem' }}>
            {errors.map((err, idx) => <li key={idx}>{err}</li>)}
          </ul>
        </div>
      )}

      {/* Desktop 2-Column Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) 340px', gap: '32px', alignItems: 'start' }}>
        
        {/* LEFT COLUMN: EVENT FORM */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
          
          {/* SECTION 1: EVENT DETAILS */}
          <div className="glass-panel" style={{ padding: '28px', borderRadius: '20px' }}>
            <h2 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'white', margin: '0 0 20px 0', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Building size={18} color="#3B82F6" /> Event Details
            </h2>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
              <div>
                <label style={{ fontSize: '0.9rem', fontWeight: 600, color: '#E2E8F0', display: 'block', marginBottom: '6px' }}>Event Name *</label>
                <input
                  ref={nameInputRef}
                  type="text"
                  value={form.name}
                  onChange={(e) => handleChange('name', e.target.value)}
                  placeholder="e.g. My College Tech Fest"
                  style={{ width: '100%', background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(139, 92, 246, 0.3)', minHeight: '48px', padding: '12px 16px', fontSize: '1rem', borderRadius: '12px', color: 'white', outline: 'none' }}
                />
              </div>

              <div>
                <label style={{ fontSize: '0.9rem', fontWeight: 600, color: '#E2E8F0', display: 'block', marginBottom: '6px' }}>Category *</label>
                <select
                  value={form.category}
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
                <label style={{ fontSize: '0.9rem', fontWeight: 600, color: '#E2E8F0', display: 'block', marginBottom: '6px' }}>Description</label>
                <textarea
                  rows={4}
                  value={form.description}
                  onChange={(e) => handleChange('description', e.target.value)}
                  placeholder="Tell attendees what your event is about, who it is for, and what they can expect."
                  style={{ width: '100%', background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(139, 92, 246, 0.3)', padding: '14px 16px', fontSize: '0.95rem', borderRadius: '12px', color: 'white', outline: 'none', resize: 'vertical' }}
                />
              </div>
            </div>
          </div>

          {/* SECTION 2: LOCATION & SCHEDULE */}
          <div className="glass-panel" style={{ padding: '28px', borderRadius: '20px' }}>
            <h2 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'white', margin: '0 0 20px 0', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <MapPin size={18} color="#10B981" /> Location & Schedule
            </h2>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
              <div>
                <label style={{ fontSize: '0.9rem', fontWeight: 600, color: '#E2E8F0', display: 'block', marginBottom: '8px' }}>Event Format</label>
                <div style={{ display: 'flex', gap: '24px' }}>
                  {['Offline', 'Online', 'Hybrid'].map((fmt) => (
                    <label key={fmt} style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '0.95rem', color: 'white', fontWeight: 600 }}>
                      <input
                        type="radio"
                        name="format"
                        checked={form.format === fmt}
                        onChange={() => handleChange('format', fmt)}
                        style={{ accentColor: '#10B981', width: '18px', height: '18px' }}
                      />
                      {fmt}
                    </label>
                  ))}
                </div>
              </div>

              {form.format !== 'Online' && (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                  <div>
                    <label style={{ fontSize: '0.9rem', fontWeight: 600, color: '#E2E8F0', display: 'block', marginBottom: '6px' }}>Venue *</label>
                    <input
                      type="text"
                      value={form.venue}
                      onChange={(e) => handleChange('venue', e.target.value)}
                      placeholder="e.g. AJIET Main Auditorium"
                      style={{ width: '100%', background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(139, 92, 246, 0.3)', minHeight: '48px', padding: '12px 16px', fontSize: '0.95rem', borderRadius: '12px', color: 'white', outline: 'none' }}
                    />
                  </div>
                  <div>
                    <label style={{ fontSize: '0.9rem', fontWeight: 600, color: '#E2E8F0', display: 'block', marginBottom: '6px' }}>City *</label>
                    <input
                      type="text"
                      value={form.city}
                      onChange={(e) => handleChange('city', e.target.value)}
                      placeholder="e.g. Mangaluru"
                      style={{ width: '100%', background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(139, 92, 246, 0.3)', minHeight: '48px', padding: '12px 16px', fontSize: '0.95rem', borderRadius: '12px', color: 'white', outline: 'none' }}
                    />
                  </div>
                </div>
              )}

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '16px' }}>
                <div>
                  <label style={{ fontSize: '0.9rem', fontWeight: 600, color: '#E2E8F0', display: 'block', marginBottom: '6px' }}>Event Date *</label>
                  <input
                    type="date"
                    value={form.date}
                    onChange={(e) => handleChange('date', e.target.value)}
                    style={{ width: '100%', background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(139, 92, 246, 0.3)', minHeight: '48px', padding: '12px 14px', fontSize: '0.95rem', borderRadius: '12px', color: 'white', outline: 'none' }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.9rem', fontWeight: 600, color: '#E2E8F0', display: 'block', marginBottom: '6px' }}>Start Time *</label>
                  <input
                    type="time"
                    value={form.startTime}
                    onChange={(e) => handleChange('startTime', e.target.value)}
                    style={{ width: '100%', background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(139, 92, 246, 0.3)', minHeight: '48px', padding: '12px 14px', fontSize: '0.95rem', borderRadius: '12px', color: 'white', outline: 'none' }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.9rem', fontWeight: 600, color: '#E2E8F0', display: 'block', marginBottom: '6px' }}>End Time *</label>
                  <input
                    type="time"
                    value={form.endTime}
                    onChange={(e) => handleChange('endTime', e.target.value)}
                    style={{ width: '100%', background: isTimeInvalid ? 'rgba(239, 68, 68, 0.2)' : 'rgba(15, 23, 42, 0.8)', border: isTimeInvalid ? '1px solid #EF4444' : '1px solid rgba(139, 92, 246, 0.3)', minHeight: '48px', padding: '12px 14px', fontSize: '0.95rem', borderRadius: '12px', color: 'white', outline: 'none' }}
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
          <div className="glass-panel" style={{ padding: '28px', borderRadius: '20px' }}>
            <h2 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'white', margin: '0 0 20px 0', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <DollarSign size={18} color="#F59E0B" /> Tickets
            </h2>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
              <div>
                <label style={{ fontSize: '0.9rem', fontWeight: 600, color: '#E2E8F0', display: 'block', marginBottom: '8px' }}>Pricing</label>
                <div style={{ display: 'flex', gap: '24px' }}>
                  {['paid', 'free'].map((pt) => (
                    <label key={pt} style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '0.95rem', color: 'white', fontWeight: 600, textTransform: 'capitalize' }}>
                      <input
                        type="radio"
                        name="pricingType"
                        checked={form.pricingType === pt}
                        onChange={() => handleChange('pricingType', pt)}
                        style={{ accentColor: '#F59E0B', width: '18px', height: '18px' }}
                      />
                      {pt} Event
                    </label>
                  ))}
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '16px' }}>
                <div>
                  <label style={{ fontSize: '0.9rem', fontWeight: 600, color: '#E2E8F0', display: 'block', marginBottom: '6px' }}>Ticket Price (₹) *</label>
                  <input
                    type="number"
                    min="0"
                    step="1"
                    disabled={form.pricingType === 'free'}
                    value={form.pricingType === 'free' ? 0 : form.price}
                    onChange={(e) => handleChange('price', e.target.value)}
                    placeholder="299"
                    style={{ width: '100%', background: form.pricingType === 'free' ? 'rgba(255,255,255,0.05)' : 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(139, 92, 246, 0.3)', minHeight: '48px', padding: '12px 16px', fontSize: '0.95rem', borderRadius: '12px', color: 'white', outline: 'none' }}
                  />
                </div>

                <div>
                  <label style={{ fontSize: '0.9rem', fontWeight: 600, color: '#E2E8F0', display: 'block', marginBottom: '6px' }}>Number of Tickets *</label>
                  <input
                    type="number"
                    min="1"
                    value={form.totalQuantity}
                    onChange={(e) => handleChange('totalQuantity', e.target.value)}
                    placeholder="150"
                    style={{ width: '100%', background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(139, 92, 246, 0.3)', minHeight: '48px', padding: '12px 16px', fontSize: '0.95rem', borderRadius: '12px', color: 'white', outline: 'none' }}
                  />
                </div>

                <div>
                  <label style={{ fontSize: '0.9rem', fontWeight: 600, color: '#E2E8F0', display: 'block', marginBottom: '6px' }}>Max Tickets / Person *</label>
                  <input
                    type="number"
                    min="1"
                    value={form.maxPerOrder}
                    onChange={(e) => handleChange('maxPerOrder', e.target.value)}
                    placeholder="5"
                    style={{ width: '100%', background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(139, 92, 246, 0.3)', minHeight: '48px', padding: '12px 16px', fontSize: '0.95rem', borderRadius: '12px', color: 'white', outline: 'none' }}
                  />
                </div>
              </div>
            </div>
          </div>

        </div>

        {/* RIGHT COLUMN: LIVE EVENT SUMMARY */}
        <div style={{ position: 'sticky', top: '24px' }}>
          <div className="glass-panel" style={{ padding: '28px', borderRadius: '20px', border: '1px solid rgba(139, 92, 246, 0.4)', boxShadow: '0 12px 36px rgba(0,0,0,0.5)' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 800, color: '#A78BFA', textTransform: 'uppercase', letterSpacing: '0.5px', display: 'block', marginBottom: '14px' }}>
              ✨ LIVE EVENT PREVIEW
            </span>

            <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'white', margin: '0 0 6px 0', lineHeight: 1.3 }}>
              {form.name.trim() || 'My College Tech Fest'}
            </h3>

            <div style={{ fontSize: '0.88rem', color: '#60A5FA', fontWeight: 700, marginBottom: '18px' }}>
              {form.category || 'Technology'} ({form.format})
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', fontSize: '0.88rem', color: '#94A3B8', borderTop: '1px solid rgba(255, 255, 255, 0.08)', borderBottom: '1px solid rgba(255, 255, 255, 0.08)', padding: '16px 0', marginBottom: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <MapPin size={16} color="#34D399" />
                <span>{form.venue ? `${form.venue}, ${form.city || 'Mangaluru'}` : (form.city || 'Mangaluru')}</span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Calendar size={16} color="#60A5FA" />
                <span>{form.date || '2026-09-30'} ({form.startTime} – {form.endTime})</span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Users size={16} color="#F59E0B" />
                <span>{form.totalQuantity || 150} Tickets ({form.maxPerOrder || 5} max/customer)</span>
              </div>
            </div>

            <div style={{ background: 'rgba(255, 255, 255, 0.04)', borderRadius: '14px', padding: '16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', border: '1px solid rgba(255,255,255,0.06)' }}>
              <div>
                <span style={{ fontSize: '0.8rem', color: '#CBD5E1', display: 'block' }}>General Pass</span>
                <strong style={{ fontSize: '1.35rem', color: '#34D399', fontWeight: 800 }}>
                  {form.pricingType === 'free' ? 'FREE' : `₹${form.price || 299}`}
                </strong>
              </div>
              <span style={{ fontSize: '0.82rem', background: 'rgba(16, 185, 129, 0.2)', color: '#34D399', padding: '6px 12px', borderRadius: '12px', fontWeight: 700 }}>
                {form.totalQuantity || 150} Available
              </span>
            </div>

            <div style={{ display: 'flex', gap: '12px', marginTop: '24px' }}>
              <button
                type="button"
                disabled={publishing || isTimeInvalid}
                onClick={handlePublish}
                style={{
                  width: '100%',
                  background: publishing || isTimeInvalid ? 'rgba(16, 185, 129, 0.4)' : 'linear-gradient(135deg, #10B981, #059669)',
                  color: 'white',
                  border: 'none',
                  padding: '14px',
                  borderRadius: '12px',
                  fontWeight: 800,
                  fontSize: '1rem',
                  cursor: publishing || isTimeInvalid ? 'not-allowed' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  boxShadow: '0 4px 16px rgba(16, 185, 129, 0.3)',
                  minHeight: '48px'
                }}
              >
                {publishing ? 'Publishing Event...' : '🚀 Publish Event'}
              </button>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
