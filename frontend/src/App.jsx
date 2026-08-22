import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Navbar from './components/Navbar';
import EventDiscovery from './components/EventDiscovery';
import RecommendationsPanel from './components/RecommendationsPanel';
import AICopilotPanel from './components/AICopilotPanel';
import BookingModal from './components/BookingModal';
import GSTInvoiceView from './components/GSTInvoiceView';
import FraudAdminDashboard from './components/FraudAdminDashboard';
import OrganizerPayouts from './components/OrganizerPayouts';
import ConcurrencyTestRunner from './components/ConcurrencyTestRunner';
import QRCheckinScanner from './components/QRCheckinScanner';
import SuperAdminDashboard from './components/SuperAdminDashboard';

import ChatMainInterface from './components/chat/ChatMainInterface';
import MyEvents from './components/organizer/MyEvents';
import EventWizard from './components/organizer/EventWizard';
import CreateEventPage from './components/organizer/CreateEventPage';

export default function App() {
  const [activeTab, setActiveTab] = useState('chat'); // chat, events, my-tickets, organizer-studio, create-event, qr-checkin, super-admin, concurrency, fraud
  const [scannerTargetEventId, setScannerTargetEventId] = useState(null);

  const [events, setEvents] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');
  const [isCopilotOpen, setIsCopilotOpen] = useState(false);
  const [bookingEvent, setBookingEvent] = useState(null);
  const [isEventWizardOpen, setIsEventWizardOpen] = useState(false);
  const [wizardInitialData, setWizardInitialData] = useState(null);

  useEffect(() => {
    fetchEvents();
    fetchRecommendations();
  }, []);

  const fetchEvents = async () => {
    try {
      const res = await axios.get('/api/v1/events');
      setEvents(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const fetchRecommendations = async () => {
    try {
      const res = await axios.get('/api/v1/recommendations');
      setRecommendations(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const handleSemanticSearch = async (query) => {
    if (!query.trim()) {
      fetchEvents();
      return;
    }
    try {
      const res = await axios.get(`/api/v1/search/semantic?q=${encodeURIComponent(query)}`);
      setEvents(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const handleNavigateToScanner = (eventId) => {
    setScannerTargetEventId(eventId);
    setActiveTab('qr-checkin');
  };

  const handleBookEventInChat = (ev) => {
    setBookingEvent(ev);
    setActiveTab('chat');
  };

  const handleOpenCreateWizard = (initialData = null) => {
    setWizardInitialData(initialData);
    setActiveTab('create-event');
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: 'var(--bg-dark)' }}>
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
        onSemanticSearch={handleSemanticSearch}
        onOpenCreateWizard={handleOpenCreateWizard}
      />

      <main style={{ flex: 1 }}>
        {activeTab === 'chat' && (
          <ChatMainInterface
            initialEvent={bookingEvent}
            onSelectEventForBooking={(ev) => handleBookEventInChat(ev)}
            onOpenCreateWizard={handleOpenCreateWizard}
          />
        )}

        {activeTab === 'create-event' && (
          <CreateEventPage
            onNavigateToExplore={() => { fetchEvents(); setActiveTab('events'); }}
            onNavigateToDashboard={() => setActiveTab('organizer-studio')}
          />
        )}

        {activeTab === 'events' && (
          <>
            <RecommendationsPanel
              recommendations={recommendations}
              onBookEvent={(ev) => handleBookEventInChat(ev)}
            />

            <EventDiscovery
              events={events}
              onBookEvent={(ev) => handleBookEventInChat(ev)}
              selectedCategory={selectedCategory}
              setSelectedCategory={setSelectedCategory}
            />
          </>
        )}

        {activeTab === 'my-tickets' && (
          <GSTInvoiceView onNavigateToChat={() => setActiveTab('chat')} />
        )}
        {activeTab === 'organizer-studio' && <MyEvents onNavigateToScanner={handleNavigateToScanner} />}
        {activeTab === 'concurrency' && <ConcurrencyTestRunner />}
        {activeTab === 'fraud' && <FraudAdminDashboard />}
        {activeTab === 'organizer' && <OrganizerPayouts />}
        {activeTab === 'qr-checkin' && <QRCheckinScanner targetEventId={scannerTargetEventId} />}
        {activeTab === 'super-admin' && <SuperAdminDashboard />}
      </main>

      <AICopilotPanel
        isOpen={isCopilotOpen}
        onClose={() => setIsCopilotOpen(false)}
        onSelectEventForBooking={(ev) => handleBookEventInChat(ev)}
        onOpenCreateWizard={handleOpenCreateWizard}
      />

      {isEventWizardOpen && (
        <EventWizard
          initialData={wizardInitialData}
          onClose={() => { setIsEventWizardOpen(false); setWizardInitialData(null); }}
          onSaveSuccess={(evData, targetTab) => { fetchEvents(); setActiveTab(targetTab || 'organizer-studio'); }}
        />
      )}


    </div>
  );
}

