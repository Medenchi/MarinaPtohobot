import { Route, Routes } from "react-router-dom";
import { useEffect } from "react";
import { telegramReady } from "@/lib/telegram";
import Landing from "@/pages/Landing";
import OutfitApp from "@/pages/OutfitApp";
import Reader from "@/pages/Reader";
import AdminLogin from "@/pages/admin/AdminLogin";
import AdminDashboard from "@/pages/admin/AdminDashboard";
import AdminOutfits from "@/pages/admin/AdminOutfits";
import AdminCourses from "@/pages/admin/AdminCourses";

export default function App() {
  useEffect(() => {
    telegramReady();
  }, []);

  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/app" element={<OutfitApp />} />
      <Route path="/reader" element={<Reader />} />
      <Route path="/admin" element={<AdminLogin />} />
      <Route path="/admin/dashboard" element={<AdminDashboard />} />
      <Route path="/admin/outfits" element={<AdminOutfits />} />
      <Route path="/admin/courses" element={<AdminCourses />} />
    </Routes>
  );
}
