import React, { useState, useEffect } from 'react';
import { X, Calendar, MapPin, DollarSign, Image, CheckCircle, AlertTriangle, ArrowRight, ArrowLeft, Plus, Trash2, Eye, Save } from 'lucide-react';
import axios from 'axios';

export default function EventWizard({ eventIdToEdit = null, onClose, onSaveSuccess }) {
  const [currentStep, setCurrentStep] = useState(1);
  const [savingDraft, setSavingDraft] = useState(false);
  const [draftSavedTime, setDraftSavedTime] = useState(null);
  const [publishErrors, setPublishErrors] = useState([]);

  // Section 57e AI Description Drafting state
  const [showAiDraftModal, setShowAiDraftModal] = useState(false);
  const [aiNotes, setAiNotes] = useState('');
  const [aiDraftLoading, setAiDraftLoading] = useState(false);

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

  const [eventId, setEventId] = useState(eventIdToEdit);

  const [formData, setFormData] = useState({
    title: '',
    category: 'Tech',
    description: '',
    date_str: '',
    start_time: '09:00',
    end_time: '18:00',
    venue: '',
    address: '',
    location: '',
    price: 0,
    total_capacity: 100,
    ticket_types: [
      { name: 'Standard Pass', price: 299, quantity: 80 },
      { name: 'VIP Pass', price: 999, quantity: 20 }
    ],
    image_url: 'https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=800&auto=format&fit=crop&q=80',
    cancellation_policy: 'Standard 24-hour cancellation policy applies. Full refund minus processing fee.',
    status: 'DRAFT'
  });

  // Load existing event data if editing
  useEffect(() => {
    if (eventIdToEdit) {
      axios.get(`/api/v1/events/${eventIdToEdit}`)
        .then(res => {
          const ev = res.data;
          setFormData({
            title: ev.title || '',
            category: ev.category || 'Tech',
            description: ev.description || '',
            date_str: ev.date_str || '',
            start_time: ev.start_time || '09:00',
            end_time: ev.end_time || '18:00',
            venue: ev.venue || '',
            address: ev.address || '',
            location: ev.location || '',
            price: ev.price || 0,
            total_capacity: ev.total_capacity || 100,
            ticket_types: (ev.ticket_types && ev.ticket_types.length > 0) ? ev.ticket_types : [
              { name: 'Standard Pass', price: ev.price || 0, quantity: ev.total_capacity || 100 }
            ],
            image_url: ev.image_url || '',
            cancellation_policy: ev.cancellation_policy || 'Standard 24-hour cancellation policy applies.',
            status: ev.status || 'DRAFT'
          });
        })
        .catch(err => console.error("Failed to load event for editing", err));
    }
  }, [eventIdToEdit]);

  // Save draft to backend (Section 45b requirement: save-as-draft at every step)
  const saveDraftToBackend = async (dataToSave = formData) => {
    setSavingDraft(true);
    setPublishErrors([]);
    try {
      const payload = {
        ...dataToSave,
        location: dataToSave.location || dataToSave.venue || 'Bengaluru',
        price: dataToSave.ticket_types && dataToSave.ticket_types.length > 0 ? Number(dataToSave.ticket_types[0].price) : Number(dataToSave.price),
        total_capacity: dataToSave.ticket_types && dataToSave.ticket_types.length > 0 
          ? dataToSave.ticket_types.reduce((sum, t) => sum + Number(t.quantity || 0), 0)
          : Number(dataToSave.total_capacity),
        status: 'DRAFT'
      };

      if (eventId) {
        await axios.put(`/api/v1/events/${eventId}`, payload);
      } else {
        const res = await axios.post('/api/v1/events', payload);
        if (res.data && res.data.id) {
          setEventId(res.data.id);
        }
      }
      setDraftSavedTime(new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }));
    } catch (err) {
      console.error("Save draft error:", err);
    } finally {
      setSavingDraft(false);
    }
  };

  const handleChange = (field, value) => {
    const updated = { ...formData, [field]: value };
    setFormData(updated);
  };

  const handleNext = () => {
    saveDraftToBackend(formData);
    if (currentStep < 5) {
      setCurrentStep(c => c + 1);
    }
  };

  const handlePrev = () => {
    if (currentStep > 1) {
      setCurrentStep(c => c - 1);
    }
  };

  // Dynamic ticket tier row handling
  const addTicketType = () => {
    const updatedTypes = [...formData.ticket_types, { name: 'Tier Ticket', price: 499, quantity: 50 }];
    const updated = { ...formData, ticket_types: updatedTypes };
    setFormData(updated);
    saveDraftToBackend(updated);
  };

  const removeTicketType = (index) => {
    const updatedTypes = formData.ticket_types.filter((_, i) => i !== index);
    const updated = { ...formData, ticket_types: updatedTypes };
    setFormData(updated);
    saveDraftToBackend(updated);
  };

  const updateTicketType = (index, field, value) => {
    const updatedTypes = [...formData.ticket_types];
    updatedTypes[index] = { ...updatedTypes[index], [field]: value };
    const updated = { ...formData, ticket_types: updatedTypes };
    setFormData(updated);
  };

  // Publish validation & submit
  const handlePublish = async () => {
    setPublishErrors([]);
    setSavingDraft(true);

    try {
      // Ensure latest state saved
      let targetId = eventId;
      if (!targetId) {
        const createRes = await axios.post('/api/v1/events', {
          ...formData,
          location: formData.location || formData.venue || 'Bengaluru',
          status: 'DRAFT'
        });
        targetId = createRes.data.id;
        setEventId(targetId);
      } else {
        await axios.put(`/api/v1/events/${targetId}`, {
          ...formData,
          location: formData.location || formData.venue || 'Bengaluru'
        });
      }

      // Execute section 45d backend validation pass
      const pubRes = await axios.post(`/api/v1/events/${targetId}/publish`);
      if (onSaveSuccess) onSaveSuccess(pubRes.data.event || pubRes.data);
      onClose();
    } catch (err) {
      if (err.response?.data?.detail?.errors) {
        setPublishErrors(err.response.data.detail.errors);
      } else if (err.response?.data?.detail) {
        setPublishErrors([err.response.data.detail]);
      } else {
        setPublishErrors(["Failed to publish event. Please ensure all required fields are complete."]);
      }
    } finally {
      setSavingDraft(false);
    }
  };

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(15, 23, 42, 0.85)', backdropFilter: 'blur(12px)', zIndex: 1100, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px' }}>
      <div className="glass-panel" style={{ width: '100%', maxWidth: '850px', maxHeight: '90vh', display: 'flex', flexDirection: 'column', overflow: 'hidden', border: '1px solid var(--border-glass)', boxShadow: '0 25px 50px -12px rgba(0,0,0,0.5)' }}>
        
        {/* Modal Header */}
        <div style={{ padding: '20px 24px', borderBottom: '1px solid var(--border-glass)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'white' }}>
              {eventId ? 'Edit Event (Wizard)' : 'Create New Event (Wizard)'}
            </h2>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Step {currentStep} of 5 — {
                currentStep === 1 ? 'Basic Info' :
                currentStep === 2 ? 'Date & Location' :
                currentStep === 3 ? 'Tickets & Pricing' :
                currentStep === 4 ? 'Poster & Media' : 'Review & Publish'
              }
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            {draftSavedTime && (
              <span style={{ fontSize: '0.75rem', color: '#34D399', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <Save size={14} /> Draft auto-saved ({draftSavedTime})
              </span>
            )}
            <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
              <X size={22} />
            </button>
          </div>
        </div>

        {/* Wizard Step Progress Bar */}
        <div style={{ display: 'flex', borderBottom: '1px solid var(--border-glass)', background: 'rgba(0,0,0,0.2)' }}>
          {['1. Basic Info', '2. Date & Venue', '3. Pricing & Tiers', '4. Media', '5. Review'].map((label, idx) => {
            const stepNum = idx + 1;
            const isActive = currentStep === stepNum;
            const isDone = currentStep > stepNum;
            return (
              <div
                key={label}
                onClick={() => { saveDraftToBackend(); setCurrentStep(stepNum); }}
                style={{
                  flex: 1,
                  padding: '12px 8px',
                  textAlign: 'center',
                  fontSize: '0.75rem',
                  fontWeight: isActive ? 700 : 500,
                  color: isActive ? '#60A5FA' : isDone ? '#34D399' : 'var(--text-muted)',
                  borderBottom: isActive ? '2px solid #3B82F6' : '2px solid transparent',
                  cursor: 'pointer',
                  background: isActive ? 'rgba(59, 130, 246, 0.08)' : 'transparent',
                  transition: 'all 0.2s'
                }}
              >
                {isDone ? '✓ ' : ''}{label}
              </div>
            );
          })}
        </div>

        {/* Modal Body / Steps */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '24px' }}>
          
          {/* STEP 1: Basic Info */}
          {currentStep === 1 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div>
                <label style={{ fontSize: '0.85rem', fontWeight: 600, color: 'white', display: 'block', marginBottom: '6px' }}>Event Title *</label>
                <input
                  type="text"
                  placeholder="e.g. India AI & Deep Learning Summit 2026"
                  value={formData.title}
                  onChange={(e) => handleChange('title', e.target.value)}
                  style={{ width: '100%', background: 'rgba(15, 23, 42, 0.7)', border: '1px solid var(--border-glass)', borderRadius: '10px', padding: '12px', color: 'white', fontSize: '0.95rem' }}
                />
              </div>

              <div>
                <label style={{ fontSize: '0.85rem', fontWeight: 600, color: 'white', display: 'block', marginBottom: '6px' }}>Category</label>
                <select
                  value={formData.category}
                  onChange={(e) => handleChange('category', e.target.value)}
                  style={{ width: '100%', background: 'rgba(15, 23, 42, 0.7)', border: '1px solid var(--border-glass)', borderRadius: '10px', padding: '12px', color: 'white', fontSize: '0.95rem' }}
                >
                  <option value="Tech">Tech</option>
                  <option value="Workshop">Workshop</option>
                  <option value="Music">Music</option>
                  <option value="Conference">Conference</option>
                  <option value="Startup">Startup</option>
                  <option value="Cultural">Cultural</option>
                </select>
              </div>

              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                  <label style={{ fontSize: '0.85rem', fontWeight: 600, color: 'white' }}>Event Description *</label>
                  <button
                    type="button"
                    onClick={() => setShowAiDraftModal(!showAiDraftModal)}
                    style={{
                      background: 'linear-gradient(135deg, #8B5CF6, #EC4899)',
                      border: 'none', color: 'white', padding: '4px 10px', borderRadius: '8px',
                      fontSize: '0.75rem', fontWeight: 700, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px'
                    }}
                  >
                    ✨ Draft with AI
                  </button>
                </div>

                {showAiDraftModal && (
                  <div style={{ background: 'rgba(15, 23, 42, 0.95)', border: '1px solid rgba(139, 92, 246, 0.5)', padding: '12px', borderRadius: '10px', marginBottom: '10px' }}>
                    <span style={{ fontSize: '0.78rem', fontWeight: 700, color: '#C4B5FD', display: 'block', marginBottom: '4px' }}>
                      AI Copywriter Assistant (§57e)
                    </span>
                    <p style={{ fontSize: '0.7rem', color: '#94A3B8', margin: '0 0 8px 0' }}>
                      Enter rough bullet points or key event highlights. AI will convert them into draft copy for your review.
                    </p>
                    <textarea
                      rows={3}
                      placeholder="e.g. 2-day AI conference in Bengaluru, 10 keynote speakers, hands-on LLM hackathon..."
                      value={aiNotes}
                      onChange={(e) => setAiNotes(e.target.value)}
                      style={{ width: '100%', background: 'rgba(255, 255, 255, 0.06)', border: '1px solid rgba(255, 255, 255, 0.15)', borderRadius: '6px', padding: '8px', color: 'white', fontSize: '0.8rem', marginBottom: '8px' }}
                    />
                    <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                      <button
                        type="button"
                        onClick={() => setShowAiDraftModal(false)}
                        style={{ background: 'transparent', border: '1px solid rgba(255, 255, 255, 0.2)', color: '#94A3B8', borderRadius: '6px', padding: '4px 10px', fontSize: '0.75rem', cursor: 'pointer' }}
                      >
                        Cancel
                      </button>
                      <button
                        type="button"
                        onClick={handleAiDraft}
                        disabled={aiDraftLoading}
                        style={{ background: 'linear-gradient(135deg, #10B981, #059669)', border: 'none', color: 'white', borderRadius: '6px', padding: '4px 12px', fontSize: '0.75rem', fontWeight: 700, cursor: 'pointer' }}
                      >
                        {aiDraftLoading ? 'Drafting...' : 'Generate Description'}
                      </button>
                    </div>
                  </div>
                )}

                <textarea
                  rows={5}
                  placeholder="Describe your event agenda, keynote speakers, session topics, target audience, and inclusions..."
                  value={formData.description}
                  onChange={(e) => handleChange('description', e.target.value)}
                  style={{ width: '100%', background: 'rgba(15, 23, 42, 0.7)', border: '1px solid var(--border-glass)', borderRadius: '10px', padding: '12px', color: 'white', fontSize: '0.95rem' }}
                />
              </div>
            </div>
          )}


          {/* STEP 2: Date & Location */}
          {currentStep === 2 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '14px' }}>
                <div>
                  <label style={{ fontSize: '0.85rem', fontWeight: 600, color: 'white', display: 'block', marginBottom: '6px' }}>Date (Str) *</label>
                  <input
                    type="text"
                    placeholder="e.g. Sat, 15 Sep 2026"
                    value={formData.date_str}
                    onChange={(e) => handleChange('date_str', e.target.value)}
                    style={{ width: '100%', background: 'rgba(15, 23, 42, 0.7)', border: '1px solid var(--border-glass)', borderRadius: '10px', padding: '12px', color: 'white', fontSize: '0.95rem' }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.85rem', fontWeight: 600, color: 'white', display: 'block', marginBottom: '6px' }}>Start Time</label>
                  <input
                    type="time"
                    value={formData.start_time}
                    onChange={(e) => handleChange('start_time', e.target.value)}
                    style={{ width: '100%', background: 'rgba(15, 23, 42, 0.7)', border: '1px solid var(--border-glass)', borderRadius: '10px', padding: '12px', color: 'white', fontSize: '0.95rem' }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.85rem', fontWeight: 600, color: 'white', display: 'block', marginBottom: '6px' }}>End Time</label>
                  <input
                    type="time"
                    value={formData.end_time}
                    onChange={(e) => handleChange('end_time', e.target.value)}
                    style={{ width: '100%', background: 'rgba(15, 23, 42, 0.7)', border: '1px solid var(--border-glass)', borderRadius: '10px', padding: '12px', color: 'white', fontSize: '0.95rem' }}
                  />
                </div>
              </div>

              <div>
                <label style={{ fontSize: '0.85rem', fontWeight: 600, color: 'white', display: 'block', marginBottom: '6px' }}>Venue Name *</label>
                <input
                  type="text"
                  placeholder="e.g. NIMHANS Convention Centre"
                  value={formData.venue}
                  onChange={(e) => {
                    handleChange('venue', e.target.value);
                    if (!formData.location) handleChange('location', `${e.target.value}, Bengaluru`);
                  }}
                  style={{ width: '100%', background: 'rgba(15, 23, 42, 0.7)', border: '1px solid var(--border-glass)', borderRadius: '10px', padding: '12px', color: 'white', fontSize: '0.95rem' }}
                />
              </div>

              <div>
                <label style={{ fontSize: '0.85rem', fontWeight: 600, color: 'white', display: 'block', marginBottom: '6px' }}>Full Location / Address</label>
                <input
                  type="text"
                  placeholder="e.g. Hosur Main Road, Lakkasandra, Bengaluru, Karnataka 560029"
                  value={formData.location}
                  onChange={(e) => handleChange('location', e.target.value)}
                  style={{ width: '100%', background: 'rgba(15, 23, 42, 0.7)', border: '1px solid var(--border-glass)', borderRadius: '10px', padding: '12px', color: 'white', fontSize: '0.95rem' }}
                />
              </div>
            </div>
          )}

          {/* STEP 3: Tickets & Pricing */}
          {currentStep === 3 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div>
                  <h4 style={{ fontSize: '1rem', fontWeight: 700, color: 'white' }}>Dynamic Ticket Tiers & Capacity</h4>
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Configure pricing categories (VIP, Early Bird, General Admission)</p>
                </div>
                <button
                  type="button"
                  onClick={addTicketType}
                  style={{ background: 'rgba(59, 130, 246, 0.2)', color: '#60A5FA', border: '1px solid #3B82F6', borderRadius: '8px', padding: '6px 12px', fontSize: '0.8rem', fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px' }}
                >
                  <Plus size={16} /> Add Ticket Tier
                </button>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {formData.ticket_types.map((tier, idx) => (
                  <div key={idx} style={{ background: 'rgba(255, 255, 255, 0.03)', border: '1px solid var(--border-glass)', borderRadius: '10px', padding: '14px', display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 40px', gap: '12px', alignItems: 'center' }}>
                    <div>
                      <label style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block' }}>Tier Name</label>
                      <input
                        type="text"
                        value={tier.name}
                        onChange={(e) => updateTicketType(idx, 'name', e.target.value)}
                        style={{ width: '100%', background: 'rgba(15, 23, 42, 0.7)', border: '1px solid var(--border-glass)', borderRadius: '6px', padding: '8px', color: 'white', fontSize: '0.85rem' }}
                      />
                    </div>
                    <div>
                      <label style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block' }}>Price (₹)</label>
                      <input
                        type="number"
                        min="0"
                        value={tier.price}
                        onChange={(e) => updateTicketType(idx, 'price', Number(e.target.value))}
                        style={{ width: '100%', background: 'rgba(15, 23, 42, 0.7)', border: '1px solid var(--border-glass)', borderRadius: '6px', padding: '8px', color: 'white', fontSize: '0.85rem' }}
                      />
                    </div>
                    <div>
                      <label style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block' }}>Quantity</label>
                      <input
                        type="number"
                        min="1"
                        value={tier.quantity}
                        onChange={(e) => updateTicketType(idx, 'quantity', Number(e.target.value))}
                        style={{ width: '100%', background: 'rgba(15, 23, 42, 0.7)', border: '1px solid var(--border-glass)', borderRadius: '6px', padding: '8px', color: 'white', fontSize: '0.85rem' }}
                      />
                    </div>
                    <div style={{ textAlign: 'center' }}>
                      {formData.ticket_types.length > 1 && (
                        <button
                          type="button"
                          onClick={() => removeTicketType(idx)}
                          style={{ background: 'none', border: 'none', color: '#F87171', cursor: 'pointer' }}
                        >
                          <Trash2 size={18} />
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>

              <div style={{ background: 'rgba(59, 130, 246, 0.1)', border: '1px solid rgba(59, 130, 246, 0.3)', padding: '12px 16px', borderRadius: '10px', display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                <span style={{ color: 'var(--text-muted)' }}>Calculated Total Capacity:</span>
                <span style={{ fontWeight: 700, color: '#60A5FA' }}>
                  {formData.ticket_types.reduce((sum, t) => sum + Number(t.quantity || 0), 0)} Seats
                </span>
              </div>
            </div>
          )}

          {/* STEP 4: Poster & Media */}
          {currentStep === 4 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div>
                <label style={{ fontSize: '0.85rem', fontWeight: 600, color: 'white', display: 'block', marginBottom: '6px' }}>Event Poster Image URL *</label>
                <input
                  type="text"
                  placeholder="https://images.unsplash.com/..."
                  value={formData.image_url}
                  onChange={(e) => handleChange('image_url', e.target.value)}
                  style={{ width: '100%', background: 'rgba(15, 23, 42, 0.7)', border: '1px solid var(--border-glass)', borderRadius: '10px', padding: '12px', color: 'white', fontSize: '0.95rem' }}
                />
              </div>

              <div>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '8px' }}>Poster Preview:</span>
                <div style={{ width: '100%', height: '220px', borderRadius: '12px', overflow: 'hidden', border: '1px solid var(--border-glass)', background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  {formData.image_url ? (
                    <img src={formData.image_url} alt="Poster Preview" style={{ width: '100%', height: '100%', objectFit: 'cover' }} onError={(e) => { e.target.style.display = 'none'; }} />
                  ) : (
                    <div style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
                      <Image size={36} />
                      <p style={{ fontSize: '0.8rem' }}>Enter image URL to view preview</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* STEP 5: Review & Publish */}
          {currentStep === 5 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <div style={{ background: 'rgba(59, 130, 246, 0.08)', border: '1px solid rgba(59, 130, 246, 0.3)', borderRadius: '12px', padding: '16px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#60A5FA', fontWeight: 700, fontSize: '0.9rem', marginBottom: '8px' }}>
                  <Eye size={18} /> Exact Buyer View Preview Card
                </div>
                <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>This preview matches what event attendees will see on the platform</p>
              </div>

              {/* Exact Card Preview */}
              <div className="glass-panel" style={{ borderRadius: '16px', overflow: 'hidden', border: '1px solid var(--border-glass)' }}>
                {formData.image_url && (
                  <img src={formData.image_url} alt="Preview" style={{ width: '100%', height: '180px', objectFit: 'cover' }} />
                )}
                <div style={{ padding: '20px' }}>
                  <span className="badge badge-grounded" style={{ marginBottom: '8px' }}>{formData.category}</span>
                  <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'white', margin: '4px 0 8px 0' }}>{formData.title || 'Untitled Event'}</h3>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '14px', lineClamp: 2 }}>{formData.description}</p>
                  
                  <div style={{ display: 'flex', gap: '16px', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '16px' }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><Calendar size={14} color="#60A5FA" /> {formData.date_str || 'Date TBD'} ({formData.start_time})</span>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><MapPin size={14} color="#34D399" /> {formData.location || 'Venue TBD'}</span>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderTop: '1px solid var(--border-glass)', paddingTop: '12px' }}>
                    <div>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block' }}>Starting Price</span>
                      <span style={{ fontSize: '1.1rem', fontWeight: 800, color: '#34D399' }}>₹{formData.ticket_types[0]?.price || formData.price}</span>
                    </div>
                    <span className="badge" style={{ background: 'rgba(255,255,255,0.08)', color: 'white' }}>
                      {formData.ticket_types.reduce((sum, t) => sum + Number(t.quantity || 0), 0)} Total Seats
                    </span>
                  </div>
                </div>
              </div>

              {/* Cancellation Policy Config */}
              <div>
                <label style={{ fontSize: '0.85rem', fontWeight: 600, color: 'white', display: 'block', marginBottom: '6px' }}>Cancellation Policy</label>
                <input
                  type="text"
                  value={formData.cancellation_policy}
                  onChange={(e) => handleChange('cancellation_policy', e.target.value)}
                  style={{ width: '100%', background: 'rgba(15, 23, 42, 0.7)', border: '1px solid var(--border-glass)', borderRadius: '10px', padding: '12px', color: 'white', fontSize: '0.85rem' }}
                />
              </div>

              {/* Publish Validation Errors */}
              {publishErrors.length > 0 && (
                <div style={{ background: 'rgba(239, 68, 68, 0.15)', border: '1px solid #F87171', borderRadius: '10px', padding: '14px', color: '#F87171' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 700, marginBottom: '6px' }}>
                    <AlertTriangle size={18} /> Section 45d Validation Checks Failed:
                  </div>
                  <ul style={{ paddingLeft: '20px', fontSize: '0.8rem', margin: 0 }}>
                    {publishErrors.map((err, i) => <li key={i}>{err}</li>)}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Modal Footer Controls */}
        <div style={{ padding: '16px 24px', borderTop: '1px solid var(--border-glass)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'rgba(0,0,0,0.3)' }}>
          <button
            type="button"
            onClick={handlePrev}
            disabled={currentStep === 1}
            style={{ background: 'transparent', border: '1px solid var(--border-glass)', color: currentStep === 1 ? 'var(--text-muted)' : 'white', padding: '10px 16px', borderRadius: '10px', cursor: currentStep === 1 ? 'not-allowed' : 'pointer', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem' }}
          >
            <ArrowLeft size={16} /> Back
          </button>

          <div style={{ display: 'flex', gap: '12px' }}>
            <button
              type="button"
              onClick={() => saveDraftToBackend()}
              disabled={savingDraft}
              style={{ background: 'rgba(255, 255, 255, 0.08)', color: 'white', border: '1px solid var(--border-glass)', padding: '10px 16px', borderRadius: '10px', cursor: 'pointer', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '6px' }}
            >
              <Save size={16} /> {savingDraft ? 'Saving Draft...' : 'Save Draft'}
            </button>

            {currentStep < 5 ? (
              <button
                type="button"
                onClick={handleNext}
                className="gradient-btn"
                style={{ padding: '10px 20px', fontSize: '0.85rem' }}
              >
                Next Step <ArrowRight size={16} />
              </button>
            ) : (
              <button
                type="button"
                onClick={handlePublish}
                disabled={savingDraft}
                className="gradient-btn"
                style={{ padding: '10px 24px', fontSize: '0.85rem', background: 'linear-gradient(135deg, #10B981, #059669)' }}
              >
                <CheckCircle size={18} /> Publish Live Event
              </button>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
