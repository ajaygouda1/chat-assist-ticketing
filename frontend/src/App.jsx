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

import MyEvents from './components/organizer/MyEvents';

export default function App() {
  const [activeTab, setActiveTab] = useState('events'); // events, my-tickets, organizer-studio, qr-checkin, super-admin, concurrency, fraud
  const [scannerTargetEventId, setScannerTargetEventId] = useState(null);

  const [events, setEvents] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');
  const [isCopilotOpen, setIsCopilotOpen] = useState(false);
  const [bookingEvent, setBookingEvent] = useState(null);

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

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        toggleCopilot={() => setIsCopilotOpen(!isCopilotOpen)}
        isCopilotOpen={isCopilotOpen}
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
        onSemanticSearch={handleSemanticSearch}
      />

      <main style={{ flex: 1 }}>
        {activeTab === 'events' && (
          <>
            <RecommendationsPanel
              recommendations={recommendations}
              onBookEvent={(ev) => setBookingEvent(ev)}
            />

            <EventDiscovery
              events={events}
              onBookEvent={(ev) => setBookingEvent(ev)}
              selectedCategory={selectedCategory}
              setSelectedCategory={setSelectedCategory}
            />
          </>
        )}

        {activeTab === 'my-tickets' && <GSTInvoiceView />}
        {activeTab === 'organizer-studio' && <MyEvents onNavigateToScanner={handleNavigateToScanner} />}
        {activeTab === 'concurrency' && <ConcurrencyTestRunner />}
        {activeTab === 'fraud' && <FraudAdminDashboard />}
        {activeTab === 'organizer' && <OrganizerPayouts />}
        {activeTab === 'qr-checkin' && <QRCheckinScanner targetEventId={scannerTargetEventId} />}
        {activeTab === 'super-admin' && <SuperAdminDashboard />}
      </main>


      {/* Booking Modal */}
      {bookingEvent && (
        <BookingModal
          event={bookingEvent}
          onClose={() => setBookingEvent(null)}
          onBookingSuccess={() => {
            fetchEvents();
            fetchRecommendations();
          }}
        />
      )}

      {/* AI Copilot Side Drawer */}
      <AICopilotPanel
        isOpen={isCopilotOpen}
        onClose={() => setIsCopilotOpen(false)}
        onSelectEventForBooking={(ev) => setBookingEvent(ev)}
      />
    </div>
  );
}
