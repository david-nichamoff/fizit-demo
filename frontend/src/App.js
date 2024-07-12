import React from "react";
import { Routes, Route } from "react-router-dom";
import Frontpage from "./pages/Frontpage/Frontpage";
import HowItWorks from "./pages/HowItWorks/HowItWorks";
import WhyFizit from "./pages/WhyFizit/WhyFizit";
import GetAQuote from "./pages/GetAQuote/GetAQuote";

function App() {
  return (
    <Routes>
      <Route path="/" element={<Frontpage />} />
      <Route path="/how-it-works" element={<HowItWorks />} />
      <Route path="/why-fizit" element={<WhyFizit />} />
      <Route path="/get-a-quote" element={<GetAQuote />} />
    </Routes>
  );
}

export default App;