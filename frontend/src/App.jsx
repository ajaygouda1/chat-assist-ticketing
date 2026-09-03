import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Navbar from './components/Navbar';
import EventDiscovery from './components/EventDiscovery';
import GSTInvoiceView from './components/GSTInvoiceView';
import FraudAdminDashboard from './components/FraudAdminDashboard';
import OrganizerPayouts from './components/OrganizerPayouts';
import ConcurrencyTestRunner from './components/ConcurrencyTestRunner';
import QRCheckinScanner from './components/QRCheckinScanner';
import SuperAdminDashboard from './components/SuperAdminDashboard';

import ChatMainInterface from './components/chat/ChatMainInterface';
import MyEvents from './components/organizer/MyEvents';
import CreateEventPage from './components/organizer/CreateEventPage';

export default function App() {
  const [activeTab, setActiveTab] = useState('chat'); // 'chat' is the core home screen
  const [scannerTargetEventId, setScannerTargetEventId] = useState(null);
  const [events, setEvents] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [bookingEvent, setBookingEvent] = useState(null);
  const [initialChatMessage, setInitialChatMessage] = useState(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  useEffect(() => {
    fetchEvents();
    if (window.location.pathname === '/gate-checkin' || window.location.hash === '#gate-checkin') {
      setActiveTab('qr-checkin');
    }
    const handlePop = () => {
      if (window.location.pathname === '/gate-checkin' || window.location.hash === '#gate-checkin') {
        setActiveTab('qr-checkin');
      }
    };
    window.addEventListener('popstate', handlePop);
    return () => window.removeEventListener('popstate', handlePop);
  }, []);

  const handleTabChange = (tab) => {
    setActiveTab(tab);
    if (tab === 'qr-checkin') {
      window.history.pushState(null, '', '/gate-checkin');
    } else if (tab === 'chat') {
      window.history.pushState(null, '', '/');
    } else {
      window.history.pushState(null, '', `/#${tab}`);
    }
  };

  const fetchEvents = async () => {
    try {
      const res = await axios.get('/api/v1/events');
      setEvents(res.data);
    } catch (err) {
      console.error('Failed to fetch events:', err);
    }
  };

  const handleBookEventInChat = (ev) => {
    setBookingEvent(ev);
    setInitialChatMessage(`Book tickets for ${ev.title}`);
    setActiveTab('chat');
  };

  const handleAskAboutEventInChat = (ev) => {
    setInitialChatMessage(`Tell me more about ${ev.title}`);
    setActiveTab('chat');
  };

  const handleNavigateToScanner = (eventId) => {
    setScannerTargetEventId(eventId);
    setActiveTab('qr-checkin');
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: 'var(--bg-primary)' }}>
      {/* Sleek Minimal Header */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={handleTabChange}
        onToggleSidebar={() => setIsSidebarOpen(prev => !prev)}
        isSidebarOpen={isSidebarOpen}
      />

      {/* Main View Shell */}
      <main style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        {activeTab === 'chat' && (
          <ChatMainInterface
            initialEvent={bookingEvent}
            initialPrompt={initialChatMessage}
            onClearInitialPrompt={() => setInitialChatMessage(null)}
            isSidebarOpen={isSidebarOpen}
            onToggleSidebar={() => setIsSidebarOpen(prev => !prev)}
            onOpenCreateEvent={() => setActiveTab('create-event')}
          />
        )}

        {activeTab === 'events' && (
          <div style={{ maxWidth: '1200px', width: '100%', margin: '0 auto', padding: '24px 20px' }}>
            <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h1 style={{ fontSize: '1.5rem', fontWeight: 700 }}>Explore Events</h1>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
                  Browse upcoming live events or ask ChatAssist to find matching experiences.
                </p>
              </div>
              <button
                onClick={() => setActiveTab('chat')}
                style={{
                  background: 'var(--accent-soft)',
                  color: 'var(--accent)',
                  border: '1px solid rgba(108, 92, 231, 0.25)',
                  borderRadius: 'var(--radius-btn)',
                  padding: '8px 16px',
                  fontWeight: 600,
                  fontSize: '0.85rem',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}
              >
                <span>✦ Ask ChatAssist</span>
              </button>
            </div>

            <EventDiscovery
              events={events}
              onBookEvent={handleBookEventInChat}
              onAskAboutEvent={handleAskAboutEventInChat}
              selectedCategory={selectedCategory}
              setSelectedCategory={setSelectedCategory}
            />
          </div>
        )}

        {activeTab === 'my-tickets' && (
          <div style={{ maxWidth: '1000px', width: '100%', margin: '0 auto', padding: '24px 20px' }}>
            <GSTInvoiceView onNavigateToChat={() => setActiveTab('chat')} />
          </div>
        )}

        {activeTab === 'create-event' && (
          <CreateEventPage
            onNavigateToExplore={() => { fetchEvents(); setActiveTab('events'); }}
            onNavigateToDashboard={() => setActiveTab('organizer-studio')}
          />
        )}

        {activeTab === 'organizer-studio' && (
          <MyEvents onNavigateToScanner={handleNavigateToScanner} />
        )}

        {activeTab === 'qr-checkin' && (
          <QRCheckinScanner targetEventId={scannerTargetEventId} />
        )}

        {activeTab === 'concurrency' && <ConcurrencyTestRunner />}
        {activeTab === 'fraud' && <FraudAdminDashboard />}
        {activeTab === 'organizer' && <OrganizerPayouts />}
        {activeTab === 'super-admin' && <SuperAdminDashboard />}
      </main>
    </div>
  );
}
