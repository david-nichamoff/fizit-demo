import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import FIZITHome from "./pages/FIZITHome/FIZITHome";
import FIZITContact from "./pages/FIZITContact/FIZITContact";  // ← You’ll create this

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<FIZITHome />} />
        <Route path="/contact" element={<FIZITContact />} />
      </Routes>
    </Router>
  );
}

export default App;