import { Outlet } from "react-router-dom";   // ← sin /dist
import ScrollToTop from "../components/ScrollToTop";
import { Navbar } from "../components/Navbar";
import { Footer } from "../components/Footer";

export const Layout = () => {
    return (
        <ScrollToTop>
            <Navbar />
            <div style={{ paddingTop: "70px", minHeight: "calc(100vh - 130px)" }}>
                <Outlet />
            </div>
            <Footer />
        </ScrollToTop>
    );
};