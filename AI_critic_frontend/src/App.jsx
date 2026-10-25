import { Routes, Route } from "react-router-dom";
import HomePage from "./pages/homepage";
import SignIn from "./components/signin";

function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route
        path="/sign-in/*"
        element={<SignIn routing="path" path="/sign-in" />}
      />
    </Routes>
  );
}

export default App;