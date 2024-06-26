import React, { useState } from 'react';
import NavBar from './NavBar';
import MainBody from './MainBody';
import SearchPage from './SearchPage';
import InfoPage from './InfoPage';
import ContactPage from './ContactPage';

const App = () => {
  const [currentPage, setCurrentPage] = useState('home');

  const renderPage = () => {
    switch (currentPage) {
      case 'home':
        return <MainBody setCurrentPage={setCurrentPage} />;
      case 'search':
        return <SearchPage header="Discover Threads" />;
      case 'info':
        return <InfoPage />;
      case 'contact':
        return <ContactPage />;
      default:
        return <MainBody setCurrentPage={setCurrentPage} />;
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-svg-bg-1 bg-cover z-0">
      <NavBar setCurrentPage={setCurrentPage} />
      <div className="flex-grow">
        {renderPage()}
      </div>
    </div>
  );
};

export default App;
