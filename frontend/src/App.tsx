import { Navigate, Route, Routes } from "react-router-dom";
import AuthGuard from "@/components/AuthGuard";
import Landing from "@/pages/Landing";
import LoginPage from "@/pages/Login";
import FlowList from "@/pages/admin/FlowList";
import Constructor from "@/pages/admin/Constructor";
import Categories from "@/pages/admin/Categories";
import Bots from "@/pages/admin/Bots";
import Outfits from "@/pages/mama/Outfits";
import Courses from "@/pages/mama/Courses";
import Bookings from "@/pages/mama/Bookings";
import Stats from "@/pages/mama/Stats";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />

      <Route
        path="/admin/login"
        element={
          <LoginPage
            role="admin"
            title="Конструктор"
            subtitle="Доступ только для владельца бота"
            successRedirect="/admin"
          />
        }
      />
      <Route
        path="/admin"
        element={
          <AuthGuard role="admin" loginPath="/admin/login">
            <FlowList />
          </AuthGuard>
        }
      />
      <Route
        path="/admin/bots"
        element={
          <AuthGuard role="admin" loginPath="/admin/login">
            <Bots />
          </AuthGuard>
        }
      />
      <Route
        path="/admin/categories"
        element={
          <AuthGuard role="admin" loginPath="/admin/login">
            <Categories />
          </AuthGuard>
        }
      />
      <Route
        path="/admin/flows/:id"
        element={
          <AuthGuard role="admin" loginPath="/admin/login">
            <Constructor />
          </AuthGuard>
        }
      />

      <Route
        path="/mama/login"
        element={
          <LoginPage
            role="mama"
            title="Контент"
            subtitle="Образы · курсы · заявки"
            successRedirect="/mama"
          />
        }
      />
      <Route
        path="/mama"
        element={
          <AuthGuard role="mama" loginPath="/mama/login">
            <Outfits />
          </AuthGuard>
        }
      />
      <Route
        path="/mama/courses"
        element={
          <AuthGuard role="mama" loginPath="/mama/login">
            <Courses />
          </AuthGuard>
        }
      />
      <Route
        path="/mama/bookings"
        element={
          <AuthGuard role="mama" loginPath="/mama/login">
            <Bookings />
          </AuthGuard>
        }
      />
      <Route
        path="/mama/stats"
        element={
          <AuthGuard role="mama" loginPath="/mama/login">
            <Stats />
          </AuthGuard>
        }
      />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
