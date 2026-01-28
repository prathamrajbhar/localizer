import React from 'react';
import Navbar from './Navbar';

const Layout = ({ children }) => {
  return (
    <div className="min-h-screen bg-gray-100">
      <Navbar />
      <main className="flex-1">
        {children}
      </main>
    </div>
  );
};

export default Layout;

