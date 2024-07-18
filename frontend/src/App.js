import React from "react";
import { Routes, Route } from "react-router-dom";
import Frontpage from "./pages/Frontpage/Frontpage";
import HowItWorks from "./pages/HowItWorks/HowItWorks";
import ForSellers from "./pages/ForSellers/ForSellers";
import ForBuyers from "./pages/ForBuyers/ForBuyers";
import GetAQuote from "./pages/GetAQuote/GetAQuote";

function App() {
  return (
    <Routes>
      <Route path="/" element={<Frontpage />} />
      <Route path="/how-it-works" element={<HowItWorks />} />
      <Route path="/for-sellers" element={<ForSellers />} />
      <Route path="/for-buyers" element={<ForBuyers />} />
      <Route path="/get-a-quote" element={<GetAQuote />} />
    </Routes>
  );
}

export default App;