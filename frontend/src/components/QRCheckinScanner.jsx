import React, { useState, useEffect, useRef } from 'react';
import { QrCode, CheckCircle2, XCircle, AlertTriangle, Camera, Search, UserCheck, ShieldCheck, RefreshCcw } from 'lucide-react';
import axios from 'axios';
import jsQR from 'jsqr';

export default function QRCheckinScanner({ targetEventId = null }) {
  const [events, setEvents] = useState([]);
  const [selectedEventId, setSelectedEventId] = useState(targetEventId ? String(targetEventId) : '');
  const [ticketInput, setTicketInput] = useState('');
  const [scanResult, setScanResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [checkedInCount, setCheckedInCount] = useState(0);

  // Camera stream & jsQR state
  const [isCameraActive, setIsCameraActive] = useState(false);
  const [cameraError, setCameraError] = useState('');
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const animFrameRef = useRef(null);

  // Sample tickets for fast testing/demo
  const [userTickets, setUserTickets] = useState([]);

  useEffect(() => {
    fetchEvents();
    fetchUserTickets();

    return () => {
      stopCamera();
    };
  }, []);

  useEffect(() => {
    if (targetEventId !== null && targetEventId !== undefined) {
      setSelectedEventId(String(targetEventId));
    }
  }, [targetEventId]);

  const fetchEvents = async () => {
    try {
      const res = await axios.get('/api/v1/events?status=ALL');
      setEvents(res.data || []);
    } catch (err) {
      console.error(err);
    }
  };

  const fetchUserTickets = async () => {
    try {
      const res = await axios.get('/api/v1/user/tickets');
      setUserTickets(res.data || []);
    } catch (err) {
      console.error(err);
    }
  };

  const startCamera = async () => {
    setCameraError('');
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setCameraError('Camera API is not supported or blocked (browsers require HTTPS or localhost for camera access).');
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment' } // rear camera on mobile devices
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      setIsCameraActive(true);
      animFrameRef.current = requestAnimationFrame(scanFrame);
    } catch (err) {
      console.error('Camera permission/access error:', err);
      if (window.location.protocol !== 'https:' && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
        setCameraError('Browser blocked camera on insecure HTTP origin. Use localhost or HTTPS, or paste the signed token/ticket ID below.');
      } else if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        setCameraError('Camera permission denied by user. Please grant camera permission or enter token manually.');
      } else {
        setCameraError(`Camera access failed: ${err.message || 'Unable to access video device'}`);
      }
      setIsCameraActive(false);
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    if (animFrameRef.current) {
      cancelAnimationFrame(animFrameRef.current);
      animFrameRef.current = null;
    }
    setIsCameraActive(false);
  };

  const scanFrame = () => {
    const v = videoRef.current;
    if (!v || v.readyState !== v.HAVE_ENOUGH_DATA) {
      animFrameRef.current = requestAnimationFrame(scanFrame);
      return;
    }

    const canvas = canvasRef.current || document.createElement('canvas');
    canvasRef.current = canvas;
    canvas.width = v.videoWidth;
    canvas.height = v.videoHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(v, 0, 0, canvas.width, canvas.height);

    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const code = jsQR(imageData.data, imageData.width, imageData.height);

    if (code && code.data) {
      setTicketInput(code.data);
      handleVerify(code.data);
      stopCamera();
    } else {
      animFrameRef.current = requestAnimationFrame(scanFrame);
    }
  };

  const handleVerify = async (inputToVerify = ticketInput, forceEventId = null) => {
    const cleanInput = (inputToVerify || '').trim();
    if (!cleanInput) return;

    setLoading(true);
    setScanResult(null);

    const rawEv = forceEventId !== null && forceEventId !== undefined ? String(forceEventId) : String(selectedEventId || '');
    const eventIdParam = rawEv && rawEv !== '' && rawEv !== '0' && rawEv.toUpperCase() !== 'ALL' ? rawEv : null;

    try {
      // Endpoint handles signed HMAC token, ticket number, and no-scope filter (§46 & §47)
      const res = await axios.post('/api/v1/tickets/verify', {
        qr_token: cleanInput,
        ticket_number: cleanInput,
        event_id: eventIdParam
      });

      setScanResult(res.data);
    } catch (err) {
      setScanResult({
        valid: false,
        status: 'INVALID',
        message: err.response?.data?.message || '❌ Invalid Ticket Token or Not Found'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmCheckin = async () => {
    if (!scanResult || !scanResult.ticket) return;
    setLoading(true);
    try {
      const res = await axios.post(`/api/v1/tickets/${scanResult.ticket.id}/check-in`, {
        ticket_id: scanResult.ticket.id,
        staff_id: "#GATE-STAFF-1"
      });

      setScanResult({
        valid: true,
        status: 'CHECKED_IN',
        message: `✅ Gate Check-In Confirmed! Welcome to ${scanResult.event_title || 'Event'}`,
        ticket_number: scanResult.ticket_number,
        event_title: scanResult.event_title
      });

      setCheckedInCount(c => c + 1);
      fetchUserTickets();
    } catch (err) {
      alert(err.response?.data?.detail || 'Check-in failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '0 24px 40px 24px' }}>
      
      {/* Header */}
      <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <QrCode color="#34D399" size={26} />
            <h2 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'white' }}>Organizer QR Gate Check-In Scanner</h2>
          </div>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
            HMAC-SHA256 Signed Token Verification & Gate Check-In Validation (§46, §47 & §53)
          </p>
        </div>

        {/* Live Checked In Counter Badge */}
        <div className="glass-panel" style={{ padding: '10px 18px', display: 'flex', alignItems: 'center', gap: '10px', border: '1px solid #34D399' }}>
          <UserCheck size={20} color="#34D399" />
          <div>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block' }}>Session Gate Check-Ins</span>
            <span style={{ fontSize: '1.1rem', fontWeight: 800, color: '#34D399' }}>{checkedInCount} Attendees Verified</span>
          </div>
        </div>
      </div>

      {/* Select Event Gate Filter */}
      <div className="glass-panel" style={{ padding: '16px 20px', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '16px' }}>
        <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'white', whiteSpace: 'nowrap' }}>Gate Event Location:</span>
        <select
          value={selectedEventId}
          onChange={(e) => setSelectedEventId(e.target.value)}
          style={{ flex: 1, background: 'rgba(15, 23, 42, 0.7)', border: '1px solid var(--border-glass)', borderRadius: '8px', padding: '10px', color: 'white', fontSize: '0.9rem' }}
        >
          <option value="">All Events (No Scope Filter)</option>
          {events.map(e => (
            <option key={e.id} value={String(e.id)}>{e.title} ({e.date_str})</option>
          ))}
        </select>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '24px' }}>
        
        {/* Scanner & Input Box */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'white', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Camera size={18} color="#60A5FA" /> Camera Scanner & Token Verification
            </h3>
            <button
              onClick={isCameraActive ? stopCamera : startCamera}
              style={{ background: isCameraActive ? 'rgba(239, 68, 68, 0.2)' : 'rgba(59, 130, 246, 0.2)', border: isCameraActive ? '1px solid #F87171' : '1px solid #60A5FA', color: isCameraActive ? '#F87171' : '#60A5FA', padding: '6px 12px', borderRadius: '8px', cursor: 'pointer', fontSize: '0.75rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px' }}
            >
              <Camera size={14} /> {isCameraActive ? 'Stop Camera' : 'Start Camera'}
            </button>
          </div>

          {/* Camera Error Alert */}
          {cameraError && (
            <div style={{ background: 'rgba(239, 68, 68, 0.15)', border: '1px solid #F87171', borderRadius: '8px', padding: '10px 14px', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <AlertTriangle size={18} color="#F87171" style={{ flexShrink: 0 }} />
              <span style={{ fontSize: '0.75rem', color: '#F87171' }}>{cameraError}</span>
            </div>
          )}

          {/* Scanner View Container */}
          <div style={{ background: 'rgba(0,0,0,0.5)', border: '2px dashed var(--border-glass)', borderRadius: '12px', padding: isCameraActive ? '8px' : '24px', textAlign: 'center', marginBottom: '20px', minHeight: '180px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              style={{ width: '100%', maxHeight: '220px', borderRadius: '8px', objectFit: 'cover', display: isCameraActive ? 'block' : 'none' }}
            />
            <canvas ref={canvasRef} style={{ display: 'none' }} />
            {!isCameraActive && (
              <>
                <QrCode size={40} color="#60A5FA" style={{ margin: '0 auto 10px auto', opacity: 0.8 }} />
                <p style={{ fontSize: '0.8rem', color: 'white', fontWeight: 600 }}>Optical Camera Stream Ready</p>
                <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Click 'Start Camera' or enter signed HMAC token below</p>
              </>
            )}
          </div>

          <form onSubmit={(e) => { e.preventDefault(); handleVerify(); }} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div>
              <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>Scan QR Code / Paste Token / Enter Ticket Number</label>
              <input
                type="text"
                placeholder="e.g. TCK-A1B2C3D4 or signed HMAC token..."
                value={ticketInput}
                onChange={(e) => setTicketInput(e.target.value)}
                style={{ width: '100%', background: 'rgba(15, 23, 42, 0.7)', border: '1px solid var(--border-glass)', borderRadius: '10px', padding: '12px 14px', color: 'white', fontSize: '0.9rem', outline: 'none' }}
              />
            </div>

            <button type="submit" className="gradient-btn" disabled={loading} style={{ justifyContent: 'center', padding: '12px' }}>
              <Search size={18} /> {loading ? 'Verifying HMAC Signature...' : 'Verify Ticket Pass'}
            </button>
          </form>

          {/* Fast Sample Tokens for Testing */}
          {userTickets.length > 0 && (
            <div style={{ marginTop: '20px', borderTop: '1px solid var(--border-glass)', paddingTop: '16px' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '8px' }}>Your Purchased Demo Pass Tokens:</span>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {userTickets.slice(0, 3).map(t => (
                  <button
                    key={t.id}
                    onClick={() => {
                      const val = (t.qr_token || t.ticket_number || '').trim();
                      setTicketInput(val);
                      const targetEvId = t.event_id ? String(t.event_id) : '';
                      if (targetEvId) {
                        setSelectedEventId(targetEvId);
                      }
                      handleVerify(val, targetEvId || selectedEventId);
                    }}
                    style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border-glass)', color: '#60A5FA', padding: '8px 12px', borderRadius: '8px', cursor: 'pointer', fontSize: '0.75rem', textAlign: 'left', display: 'flex', justifyContent: 'space-between' }}
                  >
                    <span>{t.ticket_number} ({t.event_title})</span>
                    <span style={{ color: '#34D399' }}>Scan & Auto-Select Event</span>
                  </button>
                ))}

              </div>
            </div>
          )}
        </div>

        {/* Scan Result Feedback Card */}
        <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
          {!scanResult ? (
            <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '40px 0' }}>
              <ShieldCheck size={48} style={{ opacity: 0.3, margin: '0 auto 12px auto' }} />
              <p style={{ fontSize: '0.9rem', color: 'white' }}>Awaiting Ticket Scan</p>
              <p style={{ fontSize: '0.75rem' }}>Scan QR token to verify cryptographic signature and ticket validity.</p>
            </div>
          ) : (
            <div style={{ textAlign: 'center' }}>
              <div style={{
                width: '64px',
                height: '64px',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                margin: '0 auto 16px auto',
                background: scanResult.valid && scanResult.status === 'CONFIRMED' ? 'rgba(16, 185, 129, 0.2)' : 
                            scanResult.status === 'CHECKED_IN' || scanResult.status === 'USED' ? 'rgba(59, 130, 246, 0.2)' : 'rgba(239, 68, 68, 0.2)',
                border: scanResult.valid && scanResult.status === 'CONFIRMED' ? '1px solid #34D399' : 
                        scanResult.status === 'CHECKED_IN' || scanResult.status === 'USED' ? '1px solid #60A5FA' : '1px solid #F87171'
              }}>
                {scanResult.valid && scanResult.status === 'CONFIRMED' ? (
                  <CheckCircle2 size={36} color="#34D399" />
                ) : scanResult.status === 'CHECKED_IN' || scanResult.status === 'USED' ? (
                  <UserCheck size={36} color="#60A5FA" />
                ) : (
                  <XCircle size={36} color="#F87171" />
                )}
              </div>

              <h3 style={{ fontSize: '1.2rem', fontWeight: 800, color: 'white', marginBottom: '8px' }}>
                {scanResult.message}
              </h3>

              {scanResult.event_title && (
                <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-glass)', padding: '16px', borderRadius: '12px', textAlign: 'left', margin: '16px 0' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Event</span>
                    <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'white' }}>{scanResult.event_title}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Ticket ID</span>
                    <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#60A5FA' }}>{scanResult.ticket_number}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>HMAC Signature</span>
                    <span className="badge badge-grounded">VERIFIED VALID</span>
                  </div>
                </div>
              )}

              {scanResult.valid && scanResult.status === 'CONFIRMED' && (
                <button
                  onClick={handleConfirmCheckin}
                  className="gradient-btn"
                  style={{ width: '100%', padding: '12px', justifyContent: 'center', background: 'linear-gradient(135deg, #10B981, #059669)' }}
                >
                  <UserCheck size={18} /> Confirm Attendee Gate Check-In
                </button>
              )}
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
